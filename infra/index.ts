import * as path from "path";

import * as aws from "@pulumi/aws";
import * as docker from "@pulumi/docker";
import * as pulumi from "@pulumi/pulumi";

const config = new pulumi.Config();

const appName = config.get("appName") ?? "willbe-trends";
const awsRegion = aws.config.region ?? "ap-southeast-1";
const appPort = 8000;

const containerCpu = Number(config.get("containerCpu") ?? "512");
const containerMemory = Number(config.get("containerMemory") ?? "1024");
const desiredCount = Number(config.get("desiredCount") ?? "1");

const llmProvider = config.get("llmProvider") ?? "openai";
const searchProvider = config.get("searchProvider") ?? "duckduckgo";
const openaiModel = config.get("openaiModel") ?? "gpt-4o-mini";
const anthropicModel = config.get("anthropicModel") ?? "claude-sonnet-4-20250514";
const tavilyEnabled = config.getBoolean("tavilyEnabled") ?? false;
const imageSearchEnabled = config.getBoolean("imageSearchEnabled") ?? true;
const corsOrigins = config.get("corsOrigins") ?? "";
const domainName = config.get("domainName") ?? "trending-research.wilbi.fi";
const hostedZoneName = config.get("hostedZoneName") ?? "wilbi.fi";

const openaiApiKey = config.getSecret("openaiApiKey");
const anthropicApiKey = config.getSecret("anthropicApiKey");
const tavilyApiKey = config.getSecret("tavilyApiKey");

const appPath = path.resolve(__dirname, "..");

const zone = aws.route53.getZoneOutput({
    name: hostedZoneName.endsWith(".") ? hostedZoneName : `${hostedZoneName}.`,
    privateZone: false,
});

const availabilityZones = aws.getAvailabilityZones({
    state: "available",
});

const vpc = new aws.ec2.Vpc(`${appName}-vpc`, {
    cidrBlock: "10.42.0.0/16",
    enableDnsHostnames: true,
    enableDnsSupport: true,
    tags: {
        Name: `${appName}-vpc`,
    },
});

const internetGateway = new aws.ec2.InternetGateway(`${appName}-igw`, {
    vpcId: vpc.id,
    tags: {
        Name: `${appName}-igw`,
    },
});

const publicRouteTable = new aws.ec2.RouteTable(`${appName}-public-rt`, {
    vpcId: vpc.id,
    routes: [
        {
            cidrBlock: "0.0.0.0/0",
            gatewayId: internetGateway.id,
        },
    ],
    tags: {
        Name: `${appName}-public-rt`,
    },
});

const publicSubnets = availabilityZones.then((zones) =>
    zones.names.slice(0, 2).map(
        (zone, index) =>
            new aws.ec2.Subnet(`${appName}-public-${index + 1}`, {
                vpcId: vpc.id,
                availabilityZone: zone,
                cidrBlock: `10.42.${index + 1}.0/24`,
                mapPublicIpOnLaunch: true,
                tags: {
                    Name: `${appName}-public-${index + 1}`,
                },
            }),
    ),
);

const publicSubnetRouteAssociations = publicSubnets.then((subnets) =>
    subnets.map(
        (subnet, index) =>
            new aws.ec2.RouteTableAssociation(`${appName}-public-rta-${index + 1}`, {
                subnetId: subnet.id,
                routeTableId: publicRouteTable.id,
            }),
    ),
);

const albSecurityGroup = new aws.ec2.SecurityGroup(`${appName}-alb-sg`, {
    vpcId: vpc.id,
    description: "Allow public HTTP/HTTPS traffic to the load balancer",
    ingress: [
        {
            protocol: "tcp",
            fromPort: 80,
            toPort: 80,
            cidrBlocks: ["0.0.0.0/0"],
        },
        {
            protocol: "tcp",
            fromPort: 443,
            toPort: 443,
            cidrBlocks: ["0.0.0.0/0"],
        },
    ],
    egress: [
        {
            protocol: "-1",
            fromPort: 0,
            toPort: 0,
            cidrBlocks: ["0.0.0.0/0"],
        },
    ],
});

const appSecurityGroup = new aws.ec2.SecurityGroup(`${appName}-app-sg`, {
    vpcId: vpc.id,
    description: "Allow ALB and EFS traffic to the app",
    ingress: [
        {
            protocol: "tcp",
            fromPort: appPort,
            toPort: appPort,
            securityGroups: [albSecurityGroup.id],
        },
    ],
    egress: [
        {
            protocol: "-1",
            fromPort: 0,
            toPort: 0,
            cidrBlocks: ["0.0.0.0/0"],
        },
    ],
});

const efsSecurityGroup = new aws.ec2.SecurityGroup(`${appName}-efs-sg`, {
    vpcId: vpc.id,
    description: "Allow NFS access from the app",
    ingress: [
        {
            protocol: "tcp",
            fromPort: 2049,
            toPort: 2049,
            securityGroups: [appSecurityGroup.id],
        },
    ],
    egress: [
        {
            protocol: "-1",
            fromPort: 0,
            toPort: 0,
            cidrBlocks: ["0.0.0.0/0"],
        },
    ],
});

const fileSystem = new aws.efs.FileSystem(`${appName}-efs`, {
    encrypted: true,
    tags: {
        Name: `${appName}-efs`,
    },
});

const efsMountTargets = pulumi
    .all([publicSubnets, publicSubnetRouteAssociations])
    .apply(([subnets]) =>
        subnets.map(
            (subnet, index) =>
                new aws.efs.MountTarget(`${appName}-efs-mt-${index + 1}`, {
                    fileSystemId: fileSystem.id,
                    subnetId: subnet.id,
                    securityGroups: [efsSecurityGroup.id],
                }),
        ),
    );

const efsAccessPoint = new aws.efs.AccessPoint(`${appName}-efs-ap`, {
    fileSystemId: fileSystem.id,
    posixUser: {
        gid: 1000,
        uid: 1000,
    },
    rootDirectory: {
        path: "/appdata",
        creationInfo: {
            ownerGid: 1000,
            ownerUid: 1000,
            permissions: "755",
        },
    },
});

const cluster = new aws.ecs.Cluster(`${appName}-cluster`, {
    name: `${appName}-cluster`,
});

const repository = new aws.ecr.Repository(`${appName}-repo`, {
    name: appName,
    imageScanningConfiguration: {
        scanOnPush: true,
    },
    forceDelete: true,
});

const ecrCredentials = aws.ecr.getAuthorizationTokenOutput({
    registryId: repository.registryId,
});

const image = new docker.Image(`${appName}-image`, {
    build: {
        context: appPath,
        dockerfile: path.join(appPath, "Dockerfile"),
        platform: "linux/amd64",
    },
    imageName: pulumi.interpolate`${repository.repositoryUrl}:latest`,
    registry: {
        server: repository.repositoryUrl,
        username: ecrCredentials.userName,
        password: ecrCredentials.password,
    },
});

const containerImage = pulumi
    .all([image.imageName, image.repoDigest])
    .apply(([imageName, repoDigest]) =>
        repoDigest && repoDigest.includes("@") ? repoDigest : imageName,
    );

const logGroup = new aws.cloudwatch.LogGroup(`${appName}-logs`, {
    name: `/aws/ecs/${appName}`,
    retentionInDays: 14,
});

const executionRole = new aws.iam.Role(`${appName}-execution-role`, {
    assumeRolePolicy: aws.iam.assumeRolePolicyForPrincipal({
        Service: "ecs-tasks.amazonaws.com",
    }),
});

new aws.iam.RolePolicyAttachment(`${appName}-execution-role-policy`, {
    role: executionRole.name,
    policyArn: "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy",
});

const taskRole = new aws.iam.Role(`${appName}-task-role`, {
    assumeRolePolicy: aws.iam.assumeRolePolicyForPrincipal({
        Service: "ecs-tasks.amazonaws.com",
    }),
});

function createSecret(name: string, value: pulumi.Input<string> | undefined) {
    if (!value) {
        return undefined;
    }

    const secret = new aws.secretsmanager.Secret(`${appName}-${name}`, {
        name: `${appName}/${name}`,
    });

    new aws.secretsmanager.SecretVersion(`${appName}-${name}-version`, {
        secretId: secret.id,
        secretString: value,
    });

    return secret;
}

const openaiSecret = createSecret("openaiApiKey", openaiApiKey);
const anthropicSecret = createSecret("anthropicApiKey", anthropicApiKey);
const tavilySecret = createSecret("tavilyApiKey", tavilyApiKey);

new aws.iam.RolePolicy(`${appName}-execution-secrets-policy`, {
    role: executionRole.id,
    policy: pulumi
        .all([openaiSecret?.arn, anthropicSecret?.arn, tavilySecret?.arn])
        .apply((arns) =>
            JSON.stringify({
                Version: "2012-10-17",
                Statement: arns.filter(Boolean).length
                    ? [
                          {
                              Effect: "Allow",
                              Action: ["secretsmanager:GetSecretValue"],
                              Resource: arns.filter(Boolean),
                          },
                      ]
                    : [],
            }),
        ),
});

const taskDefinition = new aws.ecs.TaskDefinition(`${appName}-task`, {
    family: `${appName}-task`,
    cpu: `${containerCpu}`,
    memory: `${containerMemory}`,
    networkMode: "awsvpc",
    requiresCompatibilities: ["FARGATE"],
    executionRoleArn: executionRole.arn,
    taskRoleArn: taskRole.arn,
    volumes: [
        {
            name: "app-data",
            efsVolumeConfiguration: {
                fileSystemId: fileSystem.id,
                transitEncryption: "ENABLED",
                authorizationConfig: {
                    accessPointId: efsAccessPoint.id,
                    iam: "DISABLED",
                },
            },
        },
    ],
    containerDefinitions: pulumi
        .all([
            containerImage,
            logGroup.name,
            openaiSecret?.arn,
            anthropicSecret?.arn,
            tavilySecret?.arn,
        ])
        .apply(([imageName, logGroupName, openaiSecretArn, anthropicSecretArn, tavilySecretArn]) =>
            JSON.stringify([
                {
                    name: "app",
                    image: imageName,
                    essential: true,
                    portMappings: [
                        {
                            containerPort: appPort,
                            hostPort: appPort,
                            protocol: "tcp",
                        },
                    ],
                    environment: [
                        { name: "WILLBE_API_HOST", value: "0.0.0.0" },
                        { name: "WILLBE_API_PORT", value: `${appPort}` },
                        { name: "WILLBE_DATABASE_URL", value: "sqlite:////app/data/willbe.db" },
                        { name: "WILLBE_PROMPTS_PATH", value: "/app/data/prompts.yaml" },
                        { name: "WILLBE_PREFERRED_SOURCES_PATH", value: "/app/data/preferred_sources.yaml" },
                        { name: "WILLBE_LLM_PROVIDER", value: llmProvider },
                        { name: "WILLBE_SEARCH_PROVIDER", value: searchProvider },
                        { name: "WILLBE_IMAGE_SEARCH_ENABLED", value: `${imageSearchEnabled}` },
                        { name: "WILLBE_CORS_ORIGINS", value: corsOrigins },
                        { name: "WILLBE_WEB_DIST", value: "/app/web/dist" },
                        { name: "OPENAI_MODEL", value: openaiModel },
                        { name: "ANTHROPIC_MODEL", value: anthropicModel },
                    ],
                    secrets: [
                        ...(openaiSecretArn
                            ? [
                                  {
                                      name: "OPENAI_API_KEY",
                                      valueFrom: openaiSecretArn,
                                  },
                              ]
                            : []),
                        ...(anthropicSecretArn
                            ? [
                                  {
                                      name: "ANTHROPIC_API_KEY",
                                      valueFrom: anthropicSecretArn,
                                  },
                              ]
                            : []),
                        ...(tavilyEnabled && tavilySecretArn
                            ? [
                                  {
                                      name: "TAVILY_API_KEY",
                                      valueFrom: tavilySecretArn,
                                  },
                              ]
                            : []),
                    ],
                    mountPoints: [
                        {
                            sourceVolume: "app-data",
                            containerPath: "/app/data",
                            readOnly: false,
                        },
                    ],
                    logConfiguration: {
                        logDriver: "awslogs",
                        options: {
                            "awslogs-group": logGroupName,
                            "awslogs-region": awsRegion,
                            "awslogs-stream-prefix": "app",
                        },
                    },
                },
            ]),
        ),
});

const loadBalancer = new aws.lb.LoadBalancer(`${appName}-alb`, {
    loadBalancerType: "application",
    securityGroups: [albSecurityGroup.id],
    subnets: publicSubnets.then((subnets) => subnets.map((subnet) => subnet.id)),
});

const targetGroup = new aws.lb.TargetGroup(`${appName}-tg`, {
    port: appPort,
    protocol: "HTTP",
    targetType: "ip",
    vpcId: vpc.id,
    healthCheck: {
        path: "/api/health",
        matcher: "200",
        healthyThreshold: 2,
        unhealthyThreshold: 2,
        interval: 30,
        timeout: 5,
    },
});

const certificate = new aws.acm.Certificate(`${appName}-cert`, {
    domainName,
    validationMethod: "DNS",
});

const validationRecords = certificate.domainValidationOptions.apply((options) =>
    options.map(
        (option, index) =>
            new aws.route53.Record(`${appName}-cert-validation-${index + 1}`, {
                zoneId: zone.zoneId,
                name: option.resourceRecordName,
                type: option.resourceRecordType,
                ttl: 60,
                records: [option.resourceRecordValue],
            }),
    ),
);

const certificateValidation = new aws.acm.CertificateValidation(`${appName}-cert-validation`, {
    certificateArn: certificate.arn,
    validationRecordFqdns: validationRecords.apply((records) => records.map((record) => record.fqdn)),
});

const httpRedirectListener = new aws.lb.Listener(`${appName}-http-listener`, {
    loadBalancerArn: loadBalancer.arn,
    port: 80,
    protocol: "HTTP",
    defaultActions: [
        {
            type: "redirect",
            redirect: {
                port: "443",
                protocol: "HTTPS",
                statusCode: "HTTP_301",
            },
        },
    ],
});

const httpsListener = new aws.lb.Listener(`${appName}-https-listener`, {
    loadBalancerArn: loadBalancer.arn,
    port: 443,
    protocol: "HTTPS",
    sslPolicy: "ELBSecurityPolicy-TLS13-1-2-Res-2021-06",
    certificateArn: certificateValidation.certificateArn,
    defaultActions: [
        {
            type: "forward",
            targetGroupArn: targetGroup.arn,
        },
    ],
});

const appDnsRecord = new aws.route53.Record(`${appName}-dns`, {
    zoneId: zone.zoneId,
    name: domainName,
    type: "A",
    aliases: [
        {
            name: loadBalancer.dnsName,
            zoneId: loadBalancer.zoneId,
            evaluateTargetHealth: true,
        },
    ],
});

const service = new aws.ecs.Service(
    `${appName}-service`,
    {
        cluster: cluster.arn,
        desiredCount,
        launchType: "FARGATE",
        taskDefinition: taskDefinition.arn,
        networkConfiguration: {
            assignPublicIp: true,
            subnets: publicSubnets.then((subnets) => subnets.map((subnet) => subnet.id)),
            securityGroups: [appSecurityGroup.id],
        },
        loadBalancers: [
            {
                targetGroupArn: targetGroup.arn,
                containerName: "app",
                containerPort: appPort,
            },
        ],
        triggers: {
            imageDigest: image.repoDigest,
        },
        waitForSteadyState: true,
    },
    {
        dependsOn: [httpsListener],
    },
);

export const url = pulumi.interpolate`https://${domainName}`;
export const loadBalancerUrl = pulumi.interpolate`http://${loadBalancer.dnsName}`;
export const region = awsRegion;
export const ecrRepositoryUrl = repository.repositoryUrl;
export const ecsClusterName = cluster.name;
export const ecsServiceName = service.name;
export const certificateArn = certificateValidation.certificateArn;
export const dnsRecord = appDnsRecord.fqdn;

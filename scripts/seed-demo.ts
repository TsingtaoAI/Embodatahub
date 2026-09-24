/**
 * TsingtaoAI 演示数据种子脚本
 *
 * 运行方式:
 *   cd ~/rslstudio/backend && npx ts-node --project tsconfig.json ../scripts/seed-demo.ts
 *
 * 登录凭据:
 *   管理员: admin@demo.com / demo123456
 *   普通用户: user@demo.com / demo123456
 */

import 'dotenv/config';
import { DataSource } from 'typeorm';

// bcrypt is in backend/node_modules; resolve it from the known location
import path from 'path';
const bcrypt = require(path.resolve(__dirname, '../backend/node_modules/bcrypt'));

import { UserEntity } from '@rslstudio/backend-common/entities/user/user.entity';
import { ProjectEntity } from '@rslstudio/backend-common/entities/project/project.entity';
import { MissionEntity } from '@rslstudio/backend-common/entities/mission/mission.entity';
import { FileEntity } from '@rslstudio/backend-common/entities/file/file.entity';
import { TopicEntity } from '@rslstudio/backend-common/entities/topic/topic.entity';
import { FileEventEntity } from '@rslstudio/backend-common/entities/file/file-event.entity';
import { AccessGroupEntity } from '@rslstudio/backend-common/entities/auth/access-group.entity';
import { GroupMembershipEntity } from '@rslstudio/backend-common/entities/auth/group-membership.entity';
import { ProjectAccessEntity } from '@rslstudio/backend-common/entities/auth/project-access.entity';
import { ApiKeyEntity } from '@rslstudio/backend-common/entities/auth/api-key.entity';
import { TagTypeEntity } from '@rslstudio/backend-common/entities/tagType/tag-type.entity';
import { MetadataEntity } from '@rslstudio/backend-common/entities/metadata/metadata.entity';
import { CategoryEntity } from '@rslstudio/backend-common/entities/category/category.entity';
import { ActionTemplateEntity } from '@rslstudio/backend-common/entities/action/action-template.entity';
import { ActionEntity } from '@rslstudio/backend-common/entities/action/action.entity';
import { WorkerEntity } from '@rslstudio/backend-common/entities/worker/worker.entity';
import { IngestionJobEntity } from '@rslstudio/backend-common/entities/file/ingestion-job.entity';
import { MissionAccessEntity } from '@rslstudio/backend-common/entities/auth/mission-access.entity';
import { ActionTriggerEntity } from '@rslstudio/backend-common/entities/action/action-trigger.entity';
import { AccountEntity } from '@rslstudio/backend-common/entities/auth/account.entity';

import {
    UserRole, AccessGroupType, AccessGroupRights,
    FileType, FileState, FileOrigin, FileEventType,
    ActionState, ActionTriggerSource, ArtifactState,
    QueueState, FileLocation, DataType, KeyTypes,
} from '@rslstudio/shared';

const dataSource = new DataSource({
    type: 'postgres',
    host: process.env.DB_HOST ?? 'localhost',
    port: Number(process.env.DB_PORT ?? 5432),
    username: process.env.DB_USER ?? 'dbuser',
    password: process.env.DB_PASSWORD ?? 'dbuserpass',
    database: process.env.DB_DATABASE ?? 'dbname',
    entities: [
        UserEntity, ProjectEntity, MissionEntity,
        FileEntity, TopicEntity, FileEventEntity,
        AccessGroupEntity, GroupMembershipEntity, ProjectAccessEntity,
        MissionAccessEntity, AccountEntity,
        ApiKeyEntity, TagTypeEntity, MetadataEntity,
        CategoryEntity, ActionTemplateEntity, ActionEntity,
        WorkerEntity, IngestionJobEntity, ActionTriggerEntity,
    ],
});

function log(step: string, msg: string) { console.log(`  ✓ [${step}] ${msg}`); }

async function main() {
    console.log('\n  TsingtaoAI 演示数据生成器\n');
    await dataSource.initialize();
    console.log('  数据库连接成功\n');

    const repos = {
        user: dataSource.getRepository(UserEntity),
        group: dataSource.getRepository(AccessGroupEntity),
        membership: dataSource.getRepository(GroupMembershipEntity),
        tagType: dataSource.getRepository(TagTypeEntity),
        category: dataSource.getRepository(CategoryEntity),
        project: dataSource.getRepository(ProjectEntity),
        mission: dataSource.getRepository(MissionEntity),
        access: dataSource.getRepository(ProjectAccessEntity),
        file: dataSource.getRepository(FileEntity),
        topic: dataSource.getRepository(TopicEntity),
        event: dataSource.getRepository(FileEventEntity),
        meta: dataSource.getRepository(MetadataEntity),
        template: dataSource.getRepository(ActionTemplateEntity),
        worker: dataSource.getRepository(WorkerEntity),
        action: dataSource.getRepository(ActionEntity),
        job: dataSource.getRepository(IngestionJobEntity),
        key: dataSource.getRepository(ApiKeyEntity),
    };

    // ── 0. CLEAR ALL DATA ────────────────────────────────────
    console.log('  清理旧数据...');
    const tables = ['file_event', 'topic', 'tag', 'file_entity', 'ingestion_job', 'action', 'action_template', 'worker', 'api_key', 'apikey', 'tag_type', 'category', 'project_access', 'mission_access', 'mission', 'project', 'group_membership', 'access_group', 'account', '"user"'];
    for (const table of tables) {
        try { await dataSource.query(`DELETE FROM ${table}`); } catch { /* table might not exist */ }
    }
    console.log('  旧数据已清理\n');

    // ── 1. USERS ────────────────────────────────────────────

    const pwHash = await bcrypt.hash('demo123456', 12);

    const adminUser = await repos.user.save({ email: 'admin@demo.com', name: '管理员', role: UserRole.ADMIN, avatarUrl: '', password: pwHash } as any);
    const normalUser = await repos.user.save({ email: 'user@demo.com', name: '演示用户', role: UserRole.USER, avatarUrl: '', password: pwHash } as any);
    log('USERS', '管理员 admin@demo.com / demo123456');
    log('USERS', '普通用户 user@demo.com / demo123456');

    // PRIMARY groups
    const adminGroup = await repos.group.save({ name: '管理员', type: AccessGroupType.PRIMARY, hidden: false } as any);
    await repos.membership.save({ canEditGroup: false, user: { uuid: adminUser.uuid }, accessGroup: { uuid: adminGroup.uuid } } as any);
    const userGroup = await repos.group.save({ name: '演示用户', type: AccessGroupType.PRIMARY, hidden: false } as any);
    await repos.membership.save({ canEditGroup: false, user: { uuid: normalUser.uuid }, accessGroup: { uuid: userGroup.uuid } } as any);
    // CUSTOM group
    const robotGroup = await repos.group.save({ name: '机器人团队', type: AccessGroupType.CUSTOM, hidden: false } as any);
    await repos.membership.save({ canEditGroup: true, user: { uuid: adminUser.uuid }, accessGroup: { uuid: robotGroup.uuid } } as any);
    await repos.membership.save({ canEditGroup: false, user: { uuid: normalUser.uuid }, accessGroup: { uuid: robotGroup.uuid } } as any);
    log('ACCESS', '机器人团队 CUSTOM group (含 2 名成员)');

    // ── 2. TAG TYPES ────────────────────────────────────────
    const tagDefs = [
        { name: '地点', datatype: DataType.STRING, description: '数据采集地点' },
        { name: '机器人编号', datatype: DataType.STRING, description: '使用的机器人型号' },
        { name: '温度', datatype: DataType.NUMBER, description: '环境温度(°C)' },
        { name: '光照条件', datatype: DataType.STRING, description: '白天/夜晚' },
        { name: '采集日期', datatype: DataType.DATE, description: '采集日期' },
        { name: '数据质量', datatype: DataType.STRING, description: '优质/一般/需检查' },
        { name: '传感器配置', datatype: DataType.STRING, description: '传感器列表' },
        { name: '备注链接', datatype: DataType.LINK, description: '相关文档链接' },
    ];
    const tagTypes = await repos.tagType.save(tagDefs.map(d => ({ ...d } as any)));
    log('TAGS', `创建了 ${tagTypes.length} 个标签类型`);

    // ── 3. PROJECTS ─────────────────────────────────────────
    const projectDefs = [
        { name: '自动驾驶感知', description: '自动驾驶场景下的多传感器感知数据采集与算法验证，涵盖高速公路和城市道路环境。' },
        { name: '四足机器人导航', description: '四足机器人在复杂地形中的自主导航与避障实验数据，包括室内和室外场景。' },
        { name: '无人机巡检', description: '无人机在工业巡检场景中的航拍与检测数据，包含电力设施和建筑结构检查。' },
    ];
    const projects: any[] = [];
    for (const d of projectDefs) {
        const p = await repos.project.save({ name: d.name, description: d.description, creator: { uuid: adminUser.uuid } } as any);
        projects.push(p);
        log('PROJ', `项目: ${d.name}`);
    }

    // ── 4. MISSIONS ─────────────────────────────────────────
    const missionDefs: Record<string, string[]> = {
        '自动驾驶感知': ['高速公路测试', '城市道路测试', '夜间驾驶测试'],
        '四足机器人导航': ['室内导航', '室外越野', '楼梯攀爬'],
        '无人机巡检': ['电力塔巡检', '建筑外立面检查', '光伏板检测'],
    };
    const missions: any[] = [];
    for (const project of projects) {
        const names = missionDefs[project.name] ?? ['默认任务'];
        for (const name of names) {
            const m = await repos.mission.save({ name, project: { uuid: project.uuid }, creator: { uuid: adminUser.uuid } } as any);
            missions.push(m);
            log('MISS', `[${project.name}] ${name}`);
        }
    }

    // ── 5. CATEGORIES ───────────────────────────────────────
    const catNames = ['传感器数据', '视觉数据', '激光雷达', '控制指令', '状态日志'];
    let ci = 0;
    for (const project of projects) {
        await repos.category.save({ name: catNames[ci % catNames.length], project: { uuid: project.uuid }, creator: { uuid: adminUser.uuid } } as any);
        await repos.category.save({ name: catNames[(ci + 1) % catNames.length], project: { uuid: project.uuid }, creator: { uuid: adminUser.uuid } } as any);
        ci++;
    }
    log('CATS', `创建了分类`);

    // ── 6. PROJECT ACCESS ───────────────────────────────────
    for (const project of projects) {
        await repos.access.save({ project: { uuid: project.uuid }, accessGroup: { uuid: robotGroup.uuid }, rights: AccessGroupRights.WRITE } as any);
    }
    log('ACCESS', '机器人团队已获得项目写入权限');

    // ── 7. FILES ────────────────────────────────────────────
    const fileDefs = [
        { name: 'highway_drive_01.bag', type: FileType.BAG, size: 157286400, topics: [
            { name: '/camera/image_raw', type: 'sensor_msgs/Image', count: 4520, freq: 30 },
            { name: '/lidar/points', type: 'sensor_msgs/PointCloud2', count: 4520, freq: 10 },
            { name: '/gps/fix', type: 'sensor_msgs/NavSatFix', count: 452, freq: 1 },
        ]},
        { name: 'urban_navigation.bag', type: FileType.BAG, size: 245366784, topics: [
            { name: '/camera/image_raw', type: 'sensor_msgs/Image', count: 8900, freq: 30 },
            { name: '/planning/path', type: 'nav_msgs/Path', count: 445, freq: 1.5 },
        ]},
        { name: 'indoor_mapping.bag', type: FileType.BAG, size: 312056832, topics: [
            { name: '/lidar/points', type: 'sensor_msgs/PointCloud2', count: 3200, freq: 10 },
            { name: '/odom', type: 'nav_msgs/Odometry', count: 3200, freq: 10 },
            { name: '/imu', type: 'sensor_msgs/Imu', count: 3200, freq: 200 },
        ]},
        { name: 'outdoor_trial.mcap', type: FileType.MCAP, size: 98304000, topics: [
            { name: '/lidar/points', type: 'sensor_msgs/PointCloud2', count: 2100, freq: 10 },
            { name: '/gps/fix', type: 'sensor_msgs/NavSatFix', count: 210, freq: 1 },
        ]},
        { name: 'stair_climb.bag', type: FileType.BAG, size: 45234560, topics: [
            { name: '/joint_states', type: 'sensor_msgs/JointState', count: 5600, freq: 50 },
            { name: '/imu', type: 'sensor_msgs/Imu', count: 5600, freq: 200 },
            { name: '/cmd_vel', type: 'geometry_msgs/Twist', count: 1200, freq: 10 },
        ]},
        { name: 'power_tower.mcap', type: FileType.MCAP, size: 234567890, topics: [
            { name: '/camera/rgb', type: 'sensor_msgs/Image', count: 1800, freq: 15 },
            { name: '/gps/fix', type: 'sensor_msgs/NavSatFix', count: 180, freq: 1 },
        ]},
        { name: 'night_drive.mcap', type: FileType.MCAP, size: 67129344, topics: [
            { name: '/camera/night', type: 'sensor_msgs/Image', count: 2800, freq: 20 },
            { name: '/lidar/points', type: 'sensor_msgs/PointCloud2', count: 2800, freq: 10 },
        ]},
        { name: 'imu_calib.bag', type: FileType.BAG, size: 12345678, topics: [
            { name: '/imu/data_raw', type: 'sensor_msgs/Imu', count: 12000, freq: 400 },
            { name: '/temperature', type: 'sensor_msgs/Temperature', count: 1200, freq: 1 },
        ]},
        { name: 'sensor_config.yml', type: FileType.YAML, size: 2048, topics: [] },
        { name: 'gps_log.yml', type: FileType.YAML, size: 1536, topics: [] },
    ];

    const allCats = await repos.category.find();
    const files: any[] = [];
    for (let i = 0; i < fileDefs.length; i++) {
        const def = fileDefs[i];
        const mission = missions[i % missions.length];
        const cat = allCats[i % allCats.length];

        const file = await repos.file.save({
            filename: def.name,
            type: def.type,
            size: def.size,
            state: FileState.OK,
            date: new Date(Date.now() - Math.random() * 30 * 86400000),
            hash: `sha256:${Math.random().toString(16).slice(2, 66)}`,
            origin: FileOrigin.UPLOAD,
            mission: { uuid: mission.uuid },
            creator: { uuid: adminUser.uuid },
            categories: [{ uuid: cat.uuid }],
        } as any);
        files.push(file);

        // Topics
        for (const t of def.topics) {
            await repos.topic.save({
                name: t.name, type: t.type, nrMessages: t.count, frequency: t.freq, messageEncoding: 'ros1',
                file: { uuid: file.uuid },
            } as any);
        }

        // Events
        await repos.event.save({ type: FileEventType.UPLOAD_COMPLETED, filenameSnapshot: def.name, file: { uuid: file.uuid }, mission: { uuid: mission.uuid } } as any);
        await repos.event.save({ type: FileEventType.TOPICS_EXTRACTED, filenameSnapshot: def.name, file: { uuid: file.uuid }, mission: { uuid: mission.uuid } } as any);

        log('FILES', `${def.name} → ${mission.name}`);
    }

    // ── 8. METADATA (tags) ──────────────────────────────────
    const metaValues = [
        { name: '地点', val: '上海嘉定' },
        { name: '机器人编号', val: 'Robot-01' },
        { name: '温度', val: '25°C' },
        { name: '光照条件', val: '白天-室外' },
        { name: '采集日期', val: '2026-06-15' },
        { name: '数据质量', val: '优质' },
    ];
    for (const mission of missions.slice(0, 3)) {
        for (const mv of metaValues) {
            const tt = tagTypes.find((t: any) => t.name === mv.name);
            if (tt) {
                await repos.meta.save({ value_string: mv.val, mission: { uuid: mission.uuid }, tagType: { uuid: tt.uuid }, creator: { uuid: adminUser.uuid } } as any);
            }
        }
    }
    log('META', '为 3 个任务创建了标签元数据');

    // ── 9. ACTION TEMPLATES ─────────────────────────────────
    const tmplDefs = [
        { name: '数据验证', desc: '验证 ROS bag 的数据完整性，检查消息频率和时间戳连续性', cpu: 1, mem: 1, gpu: -1, rt: 30 },
        { name: '元数据提取', desc: '从 ROS bag 中提取传感器配置、话题列表等元数据信息', cpu: 1, mem: 2, gpu: -1, rt: 60 },
        { name: 'BAG→MCAP', desc: '将 ROS1 bag 文件转换为 MCAP 格式', cpu: 2, mem: 4, gpu: -1, rt: 120 },
        { name: '视觉 SLAM', desc: '运行 ORB-SLAM3 处理视觉数据，生成轨迹和地图', cpu: 4, mem: 8, gpu: 4, rt: 300 },
        { name: '点云分割', desc: '对激光雷达点云进行语义分割', cpu: 4, mem: 8, gpu: 6, rt: 180 },
    ];
    for (const t of tmplDefs) {
        await repos.template.save({ name: t.name, description: t.desc, image_name: 'alpine:latest', version: 1, creator: { uuid: adminUser.uuid }, cpuCores: t.cpu, cpuMemory: t.mem, gpuMemory: t.gpu, maxRuntime: t.rt, accessRights: 0, isArchived: false } as any);
        log('TMPL', `模板: ${t.name}`);
    }

    // ── 10. WORKERS ─────────────────────────────────────────
    await repos.worker.save({ identifier: 'worker-gpu-01', hostname: 'gpu-server-01', cpuMemory: 128, cpuCores: 32, cpuModel: 'AMD EPYC 7343', gpuModel: 'NVIDIA A100 80GB', gpuMemory: 80, storage: 500000000, lastSeen: new Date(), reachable: true } as any);
    await repos.worker.save({ identifier: 'worker-cpu-01', hostname: 'compute-node-02', cpuMemory: 64, cpuCores: 16, cpuModel: 'Intel Xeon Gold 6326', gpuMemory: -1, storage: 250000000, lastSeen: new Date(), reachable: true } as any);
    log('WORKERS', '创建了 2 个计算节点');

    // ── 11. ACTIONS ─────────────────────────────────────────
    const templates = await repos.template.find();
    const workers = await repos.worker.find();
    if (templates.length >= 3 && workers.length > 0 && files.length >= 3) {
        const baseImage = { sha: null, repoDigests: null, source: 'pulled' };
        await repos.action.save({ state: ActionState.DONE, creator: { uuid: adminUser.uuid }, mission: { uuid: files[0].mission?.uuid }, template: { uuid: templates[0].uuid }, worker: { uuid: workers[0].uuid }, image: { ...baseImage } as any, exit_code: 0, triggerSource: ActionTriggerSource.MANUAL, artifacts: ArtifactState.AWAITING_ACTION, executionStartedAt: new Date(Date.now() - 10800000), executionEndedAt: new Date(Date.now() - 9000000) } as any);
        await repos.action.save({ state: ActionState.PROCESSING, creator: { uuid: adminUser.uuid }, mission: { uuid: files[1]?.mission?.uuid }, template: { uuid: templates[1]?.uuid }, worker: { uuid: workers[0]?.uuid }, image: { ...baseImage } as any, triggerSource: ActionTriggerSource.MANUAL, artifacts: ArtifactState.AWAITING_ACTION, executionStartedAt: new Date(Date.now() - 1800000) } as any);
        await repos.action.save({ state: ActionState.FAILED, creator: { uuid: adminUser.uuid }, mission: { uuid: files[2]?.mission?.uuid }, template: { uuid: templates[2]?.uuid }, worker: { uuid: workers[1]?.uuid }, image: { ...baseImage } as any, exit_code: 1, errorHint: 'MEMORY_LIMIT_EXCEEDED', triggerSource: ActionTriggerSource.MANUAL, artifacts: ArtifactState.AWAITING_ACTION, executionStartedAt: new Date(Date.now() - 7200000), executionEndedAt: new Date(Date.now() - 7000000) } as any);
        log('ACTIONS', '创建了 3 条动作执行记录');
    }

    // ── 12. INGESTION JOBS ──────────────────────────────────
    const jobStates = [QueueState.COMPLETED, QueueState.PROCESSING, QueueState.AWAITING_PROCESSING, QueueState.ERROR, QueueState.COMPLETED, QueueState.PROCESSING];
    for (let i = 0; i < Math.min(6, files.length); i++) {
        await repos.job.save({ identifier: `demo-job-${i + 1}`, displayName: `处理 ${files[i].filename}`, state: jobStates[i], location: FileLocation.S3, mission: { uuid: files[i].mission?.uuid }, creator: { uuid: adminUser.uuid }, file: { uuid: files[i].uuid } } as any);
        log('QUEUE', `队列: ${files[i].filename}`);
    }

    // ── 13. API KEYS ────────────────────────────────────────
    await repos.key.save({ key_type: KeyTypes.ACTION, rights: AccessGroupRights.WRITE, user: { uuid: adminUser.uuid } } as any);
    await repos.key.save({ key_type: KeyTypes.ACTION, rights: AccessGroupRights.READ, user: { uuid: adminUser.uuid } } as any);
    await repos.key.save({ key_type: KeyTypes.ACTION, rights: AccessGroupRights.READ, user: { uuid: normalUser.uuid } } as any);
    log('APIKEYS', '创建了 3 个 API 密钥');

    // ── SUMMARY ─────────────────────────────────────────────
    console.log('\n  ✓ 演示数据生成完毕！\n');
    console.log('  管理员:  admin@demo.com / demo123456');
    console.log('  普通用户: user@demo.com / demo123456\n');

    await dataSource.destroy();
}

main().catch(err => { console.error('种子脚本执行失败:', err); process.exit(1); });

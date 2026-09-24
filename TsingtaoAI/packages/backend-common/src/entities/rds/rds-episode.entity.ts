import { BaseEntity } from '@backend-common/entities/base-entity.entity';
import { Column, Entity, ManyToOne } from 'typeorm';
import { RdsDatasetEntity } from './rds-dataset.entity';

@Entity({ name: 'rds_episode' })
export class RdsEpisodeEntity extends BaseEntity {
    /** 所属数据集 */
    @ManyToOne(() => RdsDatasetEntity, (dataset: RdsDatasetEntity) => dataset.episodes, {
        nullable: false,
        onDelete: 'CASCADE',
    })
    dataset!: RdsDatasetEntity;

    /** Episode 在数据集中的索引 */
    @Column({ type: 'int' })
    episodeIndex!: number;

    /** Episode 时长（秒） */
    @Column({ type: 'float', default: 0 })
    durationSeconds!: number;

    /** Episode 帧数 */
    @Column({ type: 'int', default: 0 })
    length!: number;

    /** 任务描述列表 (JSON 字符串数组) */
    @Column({ type: 'simple-json', nullable: true })
    tasks!: string[] | null;

    /** 子任务列表 (JSON 对象数组) */
    @Column({ type: 'simple-json', nullable: true })
    subtasks!: Record<string, unknown>[] | null;

    /** 数据文件路径 */
    @Column({ default: '' })
    dataFile!: string;

    /** 视频文件映射 (camera_name → file_path, JSON 对象) */
    @Column({ type: 'simple-json', nullable: true })
    videoFiles!: Record<string, string> | null;
}

import { BaseEntity } from '@backend-common/entities/base-entity.entity';
import { ProjectEntity } from '@backend-common/entities/project/project.entity';
import {
    Column,
    Entity,
    ManyToOne,
    OneToMany,
} from 'typeorm';
import { RdsCleaningResultEntity } from './rds-cleaning-result.entity';
import { RdsEpisodeEntity } from './rds-episode.entity';
import { RdsFilterResultEntity } from './rds-filter-result.entity';

@Entity({ name: 'rds_dataset' })
export class RdsDatasetEntity extends BaseEntity {
    /** 数据集名称（通常为目录名或文件名） */
    @Column()
    name!: string;

    /** 数据集在文件系统上的路径 */
    @Column()
    path!: string;

    /** 数据格式标识 (lerobot_v2_1, act_hdf5, robomimic_hdf5, umi_zarr 等) */
    @Column()
    format!: string;

    /** 格式版本号 */
    @Column()
    version!: string;

    /** Episode 总数 */
    @Column({ type: 'int', default: 0 })
    totalEpisodes!: number;

    /** 所有 Episode 的总帧数 */
    @Column({ type: 'int', default: 0 })
    totalFrames!: number;

    /** 数据集帧率 (Hz) */
    @Column({ type: 'float', default: 0 })
    fps!: number;

    /** 机器人类型名称 */
    @Column({ default: '' })
    robotType!: string;

    /** 视频流 keys (JSON 数组字符串) */
    @Column({ type: 'simple-json', nullable: true })
    videoKeys!: string[] | null;

    /** 特征 schema (JSON 对象) */
    @Column({ type: 'simple-json', nullable: true })
    features!: Record<string, unknown> | null;

    /** 所属 RSLStudio 项目 */
    @ManyToOne(() => ProjectEntity, { nullable: false, onDelete: 'CASCADE' })
    project!: ProjectEntity;

    /** 关联的 Episode 列表 */
    @OneToMany(() => RdsEpisodeEntity, (episode: RdsEpisodeEntity) => episode.dataset, {
        cascade: true,
    })
    episodes?: RdsEpisodeEntity[];

    /** 关联的清洗结果 */
    @OneToMany(
        () => RdsCleaningResultEntity,
        (result: RdsCleaningResultEntity) => result.dataset,
        { cascade: true },
    )
    cleaningResults?: RdsCleaningResultEntity[];

    /** 关联的过滤结果 */
    @OneToMany(
        () => RdsFilterResultEntity,
        (result: RdsFilterResultEntity) => result.dataset,
        { cascade: true },
    )
    filterResults?: RdsFilterResultEntity[];
}

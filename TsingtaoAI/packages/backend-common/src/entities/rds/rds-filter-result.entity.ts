import { BaseEntity } from '@backend-common/entities/base-entity.entity';
import { Column, Entity, ManyToOne } from 'typeorm';
import { RdsDatasetEntity } from './rds-dataset.entity';

@Entity({ name: 'rds_filter_result' })
export class RdsFilterResultEntity extends BaseEntity {
    /** 所属数据集 */
    @ManyToOne(
        () => RdsDatasetEntity,
        (dataset: RdsDatasetEntity) => dataset.filterResults,
        { nullable: false, onDelete: 'CASCADE' },
    )
    dataset!: RdsDatasetEntity;

    /** Episode 在数据集中的索引 */
    @Column({ type: 'int' })
    episodeIndex!: number;

    /** 过滤阶段 ID (visual_quality, sudden_change, state_action_alignment, ...) */
    @Column()
    stageId!: string;

    /** 该阶段发现的问题数量 */
    @Column({ type: 'int', default: 0 })
    count!: number;

    /** 该阶段跳过原因（如果跳过则为非空字符串） */
    @Column({ default: '' })
    skippedReason!: string;

    /** 过滤发现详情 (JSON 数组) */
    @Column({ type: 'simple-json', nullable: true })
    findings!: Record<string, unknown>[] | null;
}

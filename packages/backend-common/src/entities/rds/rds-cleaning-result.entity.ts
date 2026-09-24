import { BaseEntity } from '@backend-common/entities/base-entity.entity';
import { Column, Entity, ManyToOne } from 'typeorm';
import { RdsDatasetEntity } from './rds-dataset.entity';

/** 清洗状态枚举 */
export type CleaningStatus = 'passed' | 'review' | 'excluded' | 'unscored';

@Entity({ name: 'rds_cleaning_result' })
export class RdsCleaningResultEntity extends BaseEntity {
    /** 所属数据集 */
    @ManyToOne(
        () => RdsDatasetEntity,
        (dataset: RdsDatasetEntity) => dataset.cleaningResults,
        { nullable: false, onDelete: 'CASCADE' },
    )
    dataset!: RdsDatasetEntity;

    /** Episode 在数据集中的索引 */
    @Column({ type: 'int' })
    episodeIndex!: number;

    /** 质量总分 (0-1) */
    @Column({ type: 'float', nullable: true })
    score!: number | null;

    /** 清洗状态 */
    @Column({ default: 'unscored' })
    status!: CleaningStatus;

    /** 判定来源 (auto / manual) */
    @Column({ default: 'auto' })
    source!: string;

    /** 各属性维度分数 (JSON 对象: { visual_quality: 0.8, ... }) */
    @Column({ type: 'simple-json', nullable: true })
    perAttributeScores!: Record<string, number> | null;

    /** 质检发现详情 (JSON 数组) */
    @Column({ type: 'simple-json', nullable: true })
    findings!: Record<string, unknown>[] | null;

    /** 人工审核备注 */
    @Column({ type: 'text', nullable: true })
    reviewNote!: string | null;

    /** 评分器版本 */
    @Column({ default: '' })
    scorerVersion!: string;
}

import { MigrationInterface, QueryRunner, Table, TableForeignKey, TableIndex } from 'typeorm';

export class AddRdsTables1769000000001 implements MigrationInterface {
    name = 'AddRdsTables1769000000001';

    public async up(queryRunner: QueryRunner): Promise<void> {
        // rds_dataset table
        await queryRunner.createTable(
            new Table({
                name: 'rds_dataset',
                columns: [
                    {
                        name: 'uuid',
                        type: 'uuid',
                        isPrimary: true,
                        default: 'uuid_generate_v4()',
                    },
                    {
                        name: 'createdAt',
                        type: 'timestamp',
                        default: 'now()',
                    },
                    {
                        name: 'updatedAt',
                        type: 'timestamp',
                        default: 'now()',
                    },
                    {
                        name: 'deletedAt',
                        type: 'timestamp',
                        isNullable: true,
                    },
                    {
                        name: 'name',
                        type: 'character varying',
                    },
                    {
                        name: 'path',
                        type: 'character varying',
                    },
                    {
                        name: 'format',
                        type: 'character varying',
                    },
                    {
                        name: 'version',
                        type: 'character varying',
                    },
                    {
                        name: 'totalEpisodes',
                        type: 'integer',
                        default: 0,
                    },
                    {
                        name: 'totalFrames',
                        type: 'integer',
                        default: 0,
                    },
                    {
                        name: 'fps',
                        type: 'float',
                        default: 0,
                    },
                    {
                        name: 'robotType',
                        type: 'character varying',
                        default: "''",
                    },
                    {
                        name: 'videoKeys',
                        type: 'json',
                        isNullable: true,
                    },
                    {
                        name: 'features',
                        type: 'json',
                        isNullable: true,
                    },
                    {
                        name: 'projectUuid',
                        type: 'uuid',
                    },
                ],
            }),
            true,
        );

        // rds_episode table
        await queryRunner.createTable(
            new Table({
                name: 'rds_episode',
                columns: [
                    {
                        name: 'uuid',
                        type: 'uuid',
                        isPrimary: true,
                        default: 'uuid_generate_v4()',
                    },
                    {
                        name: 'createdAt',
                        type: 'timestamp',
                        default: 'now()',
                    },
                    {
                        name: 'updatedAt',
                        type: 'timestamp',
                        default: 'now()',
                    },
                    {
                        name: 'deletedAt',
                        type: 'timestamp',
                        isNullable: true,
                    },
                    {
                        name: 'episodeIndex',
                        type: 'integer',
                    },
                    {
                        name: 'durationSeconds',
                        type: 'float',
                        default: 0,
                    },
                    {
                        name: 'length',
                        type: 'integer',
                        default: 0,
                    },
                    {
                        name: 'tasks',
                        type: 'json',
                        isNullable: true,
                    },
                    {
                        name: 'subtasks',
                        type: 'json',
                        isNullable: true,
                    },
                    {
                        name: 'dataFile',
                        type: 'character varying',
                        default: "''",
                    },
                    {
                        name: 'videoFiles',
                        type: 'json',
                        isNullable: true,
                    },
                    {
                        name: 'datasetUuid',
                        type: 'uuid',
                    },
                ],
            }),
            true,
        );

        // rds_cleaning_result table
        await queryRunner.createTable(
            new Table({
                name: 'rds_cleaning_result',
                columns: [
                    {
                        name: 'uuid',
                        type: 'uuid',
                        isPrimary: true,
                        default: 'uuid_generate_v4()',
                    },
                    {
                        name: 'createdAt',
                        type: 'timestamp',
                        default: 'now()',
                    },
                    {
                        name: 'updatedAt',
                        type: 'timestamp',
                        default: 'now()',
                    },
                    {
                        name: 'deletedAt',
                        type: 'timestamp',
                        isNullable: true,
                    },
                    {
                        name: 'episodeIndex',
                        type: 'integer',
                    },
                    {
                        name: 'score',
                        type: 'float',
                        isNullable: true,
                    },
                    {
                        name: 'status',
                        type: 'character varying',
                        default: "'unscored'",
                    },
                    {
                        name: 'source',
                        type: 'character varying',
                        default: "'auto'",
                    },
                    {
                        name: 'perAttributeScores',
                        type: 'json',
                        isNullable: true,
                    },
                    {
                        name: 'findings',
                        type: 'json',
                        isNullable: true,
                    },
                    {
                        name: 'reviewNote',
                        type: 'character varying',
                        isNullable: true,
                    },
                    {
                        name: 'scorerVersion',
                        type: 'character varying',
                        default: "''",
                    },
                    {
                        name: 'datasetUuid',
                        type: 'uuid',
                    },
                ],
            }),
            true,
        );

        // rds_filter_result table
        await queryRunner.createTable(
            new Table({
                name: 'rds_filter_result',
                columns: [
                    {
                        name: 'uuid',
                        type: 'uuid',
                        isPrimary: true,
                        default: 'uuid_generate_v4()',
                    },
                    {
                        name: 'createdAt',
                        type: 'timestamp',
                        default: 'now()',
                    },
                    {
                        name: 'updatedAt',
                        type: 'timestamp',
                        default: 'now()',
                    },
                    {
                        name: 'deletedAt',
                        type: 'timestamp',
                        isNullable: true,
                    },
                    {
                        name: 'episodeIndex',
                        type: 'integer',
                    },
                    {
                        name: 'stageId',
                        type: 'character varying',
                    },
                    {
                        name: 'count',
                        type: 'integer',
                        default: 0,
                    },
                    {
                        name: 'skippedReason',
                        type: 'character varying',
                        default: "''",
                    },
                    {
                        name: 'findings',
                        type: 'json',
                        isNullable: true,
                    },
                    {
                        name: 'datasetUuid',
                        type: 'uuid',
                    },
                ],
            }),
            true,
        );

        // Indexes
        await queryRunner.createIndex(
            'rds_dataset',
            new TableIndex({
                name: 'IDX_rds_dataset_deletedAt',
                columnNames: ['deletedAt'],
            }),
        );
        await queryRunner.createIndex(
            'rds_dataset',
            new TableIndex({
                name: 'IDX_rds_dataset_projectUuid',
                columnNames: ['projectUuid'],
            }),
        );
        await queryRunner.createIndex(
            'rds_episode',
            new TableIndex({
                name: 'IDX_rds_episode_deletedAt',
                columnNames: ['deletedAt'],
            }),
        );
        await queryRunner.createIndex(
            'rds_episode',
            new TableIndex({
                name: 'IDX_rds_episode_datasetUuid',
                columnNames: ['datasetUuid'],
            }),
        );
        await queryRunner.createIndex(
            'rds_cleaning_result',
            new TableIndex({
                name: 'IDX_rds_cleaning_result_deletedAt',
                columnNames: ['deletedAt'],
            }),
        );
        await queryRunner.createIndex(
            'rds_cleaning_result',
            new TableIndex({
                name: 'IDX_rds_cleaning_result_datasetUuid',
                columnNames: ['datasetUuid'],
            }),
        );
        await queryRunner.createIndex(
            'rds_filter_result',
            new TableIndex({
                name: 'IDX_rds_filter_result_deletedAt',
                columnNames: ['deletedAt'],
            }),
        );
        await queryRunner.createIndex(
            'rds_filter_result',
            new TableIndex({
                name: 'IDX_rds_filter_result_datasetUuid',
                columnNames: ['datasetUuid'],
            }),
        );

        // Foreign keys
        await queryRunner.createForeignKey(
            'rds_dataset',
            new TableForeignKey({
                name: 'FK_rds_dataset_project',
                columnNames: ['projectUuid'],
                referencedTableName: 'project',
                referencedColumnNames: ['uuid'],
                onDelete: 'CASCADE',
            }),
        );
        await queryRunner.createForeignKey(
            'rds_episode',
            new TableForeignKey({
                name: 'FK_rds_episode_dataset',
                columnNames: ['datasetUuid'],
                referencedTableName: 'rds_dataset',
                referencedColumnNames: ['uuid'],
                onDelete: 'CASCADE',
            }),
        );
        await queryRunner.createForeignKey(
            'rds_cleaning_result',
            new TableForeignKey({
                name: 'FK_rds_cleaning_result_dataset',
                columnNames: ['datasetUuid'],
                referencedTableName: 'rds_dataset',
                referencedColumnNames: ['uuid'],
                onDelete: 'CASCADE',
            }),
        );
        await queryRunner.createForeignKey(
            'rds_filter_result',
            new TableForeignKey({
                name: 'FK_rds_filter_result_dataset',
                columnNames: ['datasetUuid'],
                referencedTableName: 'rds_dataset',
                referencedColumnNames: ['uuid'],
                onDelete: 'CASCADE',
            }),
        );
    }

    public async down(queryRunner: QueryRunner): Promise<void> {
        // Drop foreign keys
        await queryRunner.dropForeignKey('rds_filter_result', 'FK_rds_filter_result_dataset');
        await queryRunner.dropForeignKey('rds_cleaning_result', 'FK_rds_cleaning_result_dataset');
        await queryRunner.dropForeignKey('rds_episode', 'FK_rds_episode_dataset');
        await queryRunner.dropForeignKey('rds_dataset', 'FK_rds_dataset_project');

        // Drop indexes
        await queryRunner.dropIndex('rds_filter_result', 'IDX_rds_filter_result_datasetUuid');
        await queryRunner.dropIndex('rds_filter_result', 'IDX_rds_filter_result_deletedAt');
        await queryRunner.dropIndex('rds_cleaning_result', 'IDX_rds_cleaning_result_datasetUuid');
        await queryRunner.dropIndex('rds_cleaning_result', 'IDX_rds_cleaning_result_deletedAt');
        await queryRunner.dropIndex('rds_episode', 'IDX_rds_episode_datasetUuid');
        await queryRunner.dropIndex('rds_episode', 'IDX_rds_episode_deletedAt');
        await queryRunner.dropIndex('rds_dataset', 'IDX_rds_dataset_projectUuid');
        await queryRunner.dropIndex('rds_dataset', 'IDX_rds_dataset_deletedAt');

        // Drop tables
        await queryRunner.dropTable('rds_filter_result', true);
        await queryRunner.dropTable('rds_cleaning_result', true);
        await queryRunner.dropTable('rds_episode', true);
        await queryRunner.dropTable('rds_dataset', true);
    }
}

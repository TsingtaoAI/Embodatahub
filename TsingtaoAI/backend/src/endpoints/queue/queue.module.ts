import QueueService from '@/services/queue.service';
import { AccessGroupEntity } from '@rslstudio/backend-common';
import { ActionEntity } from '@rslstudio/backend-common/entities/action/action.entity';
import { AccountEntity } from '@rslstudio/backend-common/entities/auth/account.entity';
import { FileEventEntity } from '@rslstudio/backend-common/entities/file/file-event.entity';
import { FileEntity } from '@rslstudio/backend-common/entities/file/file.entity';
import { IngestionJobEntity } from '@rslstudio/backend-common/entities/file/ingestion-job.entity';
import { MetadataEntity } from '@rslstudio/backend-common/entities/metadata/metadata.entity';
import { MissionEntity } from '@rslstudio/backend-common/entities/mission/mission.entity';
import { ProjectEntity } from '@rslstudio/backend-common/entities/project/project.entity';
import { WorkerEntity } from '@rslstudio/backend-common/entities/worker/worker.entity';
import { StorageModule } from '@rslstudio/backend-common/modules/storage/storage.module';
import { Module } from '@nestjs/common';
import { TypeOrmModule } from '@nestjs/typeorm';
import { makeGaugeProvider } from '@willsoto/nestjs-prometheus';
import { TriggerModule } from '../trigger/trigger.module';

@Module({
    imports: [
        StorageModule,
        TriggerModule,
        TypeOrmModule.forFeature([
            IngestionJobEntity,
            FileEventEntity,
            MissionEntity,
            AccountEntity,
            AccessGroupEntity,
            ProjectEntity,
            MetadataEntity,
            FileEntity,
            WorkerEntity,
            ActionEntity,
        ]),
    ],
    providers: [
        QueueService,
        makeGaugeProvider({
            name: 'backend_online_workers',
            help: 'Number of online workers',
            labelNames: ['queue'],
        }),
        makeGaugeProvider({
            name: 'backend_pending_jobs',
            help: 'Number of pending jobs',
            labelNames: ['queue'],
        }),
        makeGaugeProvider({
            name: 'backend_active_jobs',
            help: 'Number of active jobs',
            labelNames: ['queue'],
        }),
        makeGaugeProvider({
            name: 'backend_completed_jobs',
            help: 'Number of completed jobs',
            labelNames: ['queue'],
        }),
        makeGaugeProvider({
            name: 'backend_failed_jobs',
            help: 'Number of completed jobs',
            labelNames: ['queue'],
        }),
    ],
    controllers: [],
    exports: [QueueService],
})
// eslint-disable-next-line @typescript-eslint/no-extraneous-class
export class QueueModule {}

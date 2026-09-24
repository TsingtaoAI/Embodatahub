import { ActionService } from '@/services/action.service';
import { AccessGroupEntity } from '@rslstudio/backend-common';
import { ActionTemplateEntity } from '@rslstudio/backend-common/entities/action/action-template.entity';
import { ActionEntity } from '@rslstudio/backend-common/entities/action/action.entity';
import { AccountEntity } from '@rslstudio/backend-common/entities/auth/account.entity';
import { FileEntity } from '@rslstudio/backend-common/entities/file/file.entity';
import { MetadataEntity } from '@rslstudio/backend-common/entities/metadata/metadata.entity';
import { MissionEntity } from '@rslstudio/backend-common/entities/mission/mission.entity';
import { ProjectEntity } from '@rslstudio/backend-common/entities/project/project.entity';
import { ActionDispatcherModule } from '@rslstudio/backend-common/modules/action-dispatcher/action-dispatcher.module';
import { StorageModule } from '@rslstudio/backend-common/modules/storage/storage.module';
import { Module } from '@nestjs/common';
import { TypeOrmModule } from '@nestjs/typeorm';
import { ActionGuardService } from '../auth/action-guard.service';
import { FileModule } from '../file/file.module';
import { QueueModule } from '../queue/queue.module';
import { ActionsController } from './action.controller';

@Module({
    imports: [
        TypeOrmModule.forFeature([
            ActionEntity,
            ActionTemplateEntity,
            AccessGroupEntity,
            ProjectEntity,
            MissionEntity,
            AccountEntity,
            MetadataEntity,
            FileEntity,
        ]),
        QueueModule,
        StorageModule,
        StorageModule,
        ActionDispatcherModule,
        FileModule,
    ],
    providers: [ActionService, ActionGuardService],
    exports: [ActionService],
    controllers: [ActionsController],
})
// eslint-disable-next-line @typescript-eslint/no-extraneous-class
export class ActionModule {}

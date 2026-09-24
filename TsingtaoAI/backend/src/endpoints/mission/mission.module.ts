import { MissionService } from '@/services/mission.service';
import { TagService } from '@/services/tag.service';
import { UserService } from '@/services/user.service';
import { AccessGroupEntity } from '@rslstudio/backend-common';
import { AccountEntity } from '@rslstudio/backend-common/entities/auth/account.entity';
import { MetadataEntity } from '@rslstudio/backend-common/entities/metadata/metadata.entity';
import { MissionEntity } from '@rslstudio/backend-common/entities/mission/mission.entity';
import { ProjectEntity } from '@rslstudio/backend-common/entities/project/project.entity';
import { TagTypeEntity } from '@rslstudio/backend-common/entities/tagType/tag-type.entity';
import { StorageModule } from '@rslstudio/backend-common/modules/storage/storage.module';
import { Module } from '@nestjs/common';
import { TypeOrmModule } from '@nestjs/typeorm';
import { MissionController } from './mission.controller';

@Module({
    imports: [
        TypeOrmModule.forFeature([
            MissionEntity,
            ProjectEntity,
            AccountEntity,
            AccessGroupEntity,
            MetadataEntity,
            TagTypeEntity,
        ]),
        StorageModule,
    ],
    providers: [MissionService, UserService, TagService],
    controllers: [MissionController],
    exports: [MissionService],
})
// eslint-disable-next-line @typescript-eslint/no-extraneous-class
export class MissionModule {}

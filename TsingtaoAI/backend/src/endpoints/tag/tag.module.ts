import { TagService } from '@/services/tag.service';
import { AccessGroupEntity, ApiKeyEntity } from '@rslstudio/backend-common';
import { AccountEntity } from '@rslstudio/backend-common/entities/auth/account.entity';
import { MetadataEntity } from '@rslstudio/backend-common/entities/metadata/metadata.entity';
import { MissionEntity } from '@rslstudio/backend-common/entities/mission/mission.entity';
import { ProjectEntity } from '@rslstudio/backend-common/entities/project/project.entity';
import { TagTypeEntity } from '@rslstudio/backend-common/entities/tagType/tag-type.entity';
import { Module } from '@nestjs/common';
import { TypeOrmModule } from '@nestjs/typeorm';
import { TagController } from './tag.controller';

@Module({
    imports: [
        TypeOrmModule.forFeature([
            MetadataEntity,
            TagTypeEntity,
            MissionEntity,
            AccessGroupEntity,
            ProjectEntity,
            AccountEntity,
            ApiKeyEntity,
        ]),
    ],
    providers: [TagService],
    controllers: [TagController],
    exports: [TagService],
})
// eslint-disable-next-line @typescript-eslint/no-extraneous-class
export class TagModule {}

import { AccessService } from '@/services/access.service';
import { ProjectService } from '@/services/project.service';
import { AccessGroupEntity, ProjectEntity } from '@rslstudio/backend-common';
import { AccountEntity } from '@rslstudio/backend-common/entities/auth/account.entity';
import { ProjectAccessEntity } from '@rslstudio/backend-common/entities/auth/project-access.entity';
import { TagTypeEntity } from '@rslstudio/backend-common/entities/tagType/tag-type.entity';
import { Module } from '@nestjs/common';
import { TypeOrmModule } from '@nestjs/typeorm';
import { OldProjectController, ProjectController } from './project.controller';

@Module({
    imports: [
        TypeOrmModule.forFeature([
            ProjectEntity,
            AccountEntity,
            AccessGroupEntity,
            TagTypeEntity,
            ProjectAccessEntity,
        ]),
    ],
    providers: [ProjectService, AccessService],
    exports: [ProjectService],
    controllers: [ProjectController, OldProjectController],
})
// eslint-disable-next-line @typescript-eslint/no-extraneous-class
export class ProjectModule {}

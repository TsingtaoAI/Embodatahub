import { AccessService } from '@/services/access.service';
import { AccessGroupEntity, ProjectEntity } from '@rslstudio/backend-common';
import { GroupMembershipEntity } from '@rslstudio/backend-common/entities/auth/group-membership.entity';
import { ProjectAccessEntity } from '@rslstudio/backend-common/entities/auth/project-access.entity';
import { UserEntity } from '@rslstudio/backend-common/entities/user/user.entity';
import { Module } from '@nestjs/common';
import { TypeOrmModule } from '@nestjs/typeorm';
import { AccessController } from './access.controller';

@Module({
    imports: [
        TypeOrmModule.forFeature([
            UserEntity,
            AccessGroupEntity,
            GroupMembershipEntity,
            ProjectEntity,
            ProjectAccessEntity,
        ]),
    ],
    providers: [AccessService],
    controllers: [AccessController],
    exports: [AccessService],
})
// eslint-disable-next-line @typescript-eslint/no-extraneous-class
export class AccessModule {}

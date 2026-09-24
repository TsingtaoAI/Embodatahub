import {
    ProjectEntity,
    RdsCleaningResultEntity,
    RdsDatasetEntity,
    RdsEpisodeEntity,
    RdsFilterResultEntity,
} from '@rslstudio/backend-common';
import { Module } from '@nestjs/common';
import { TypeOrmModule } from '@nestjs/typeorm';
import { RdsController } from './rds.controller';
import { RdsService } from './rds.service';

@Module({
    imports: [
        TypeOrmModule.forFeature([
            RdsDatasetEntity,
            RdsEpisodeEntity,
            RdsCleaningResultEntity,
            RdsFilterResultEntity,
            ProjectEntity,
        ]),
    ],
    providers: [RdsService],
    exports: [RdsService],
    controllers: [RdsController],
})
export class RdsModule {}

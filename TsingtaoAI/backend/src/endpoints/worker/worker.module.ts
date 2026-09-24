import { WorkerService } from '@/services/worker.service';
import { WorkerEntity } from '@rslstudio/backend-common/entities/worker/worker.entity';
import { Module } from '@nestjs/common';
import { TypeOrmModule } from '@nestjs/typeorm';
import { WorkerController } from './worker.controller';

@Module({
    imports: [TypeOrmModule.forFeature([WorkerEntity])],
    controllers: [WorkerController],
    providers: [WorkerService],
    exports: [WorkerService],
})
// eslint-disable-next-line @typescript-eslint/no-extraneous-class
export class WorkerModule {}

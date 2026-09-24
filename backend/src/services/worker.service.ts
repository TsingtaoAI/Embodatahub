import { ActionWorkersDto } from '@rslstudio/api-dto';
import { WorkerEntity } from '@rslstudio/backend-common/entities/worker/worker.entity';
import { Injectable } from '@nestjs/common';
import { InjectRepository } from '@nestjs/typeorm';
import { plainToInstance } from 'class-transformer';
import { validateSync } from 'class-validator';
import { Repository } from 'typeorm';

@Injectable()
export class WorkerService {
    constructor(
        @InjectRepository(WorkerEntity)
        private workerRepository: Repository<WorkerEntity>,
    ) {}

    async findAll(): Promise<ActionWorkersDto> {
        const workers = await this.workerRepository.find();

        // deduplicate workers by hostname get last seen worker
        // eslint-disable-next-line unicorn/no-array-reduce
        const workerMap = workers.reduce(
            (accumulator: Record<string, WorkerEntity>, worker) => {
                if (
                    // eslint-disable-next-line @typescript-eslint/no-unnecessary-condition
                    !accumulator[worker.hostname] ||
                    accumulator[worker.hostname].lastSeen < worker.lastSeen
                ) {
                    accumulator[worker.hostname] = worker;
                }
                return accumulator;
            },
            {},
        );

        const now = Date.now();
        const REACHABLE_TIMEOUT_MS = 5 * 60 * 1000; // 5 分钟内有心跳视为在线

        const count = Object.keys(workerMap).length;
        const result = {
            count,
            data: Object.values(workerMap).map((worker) => ({
                // eslint-disable-next-line @typescript-eslint/no-misused-spread
                ...worker,
                gpuModel: worker.gpuModel ?? null,
                // 基于 lastSeen 动态判断在线状态（而非仅依赖可能过时的 DB 字段）
                reachable:
                    now - new Date(worker.lastSeen).getTime() <
                    REACHABLE_TIMEOUT_MS,
            })),
            skip: 0,
            take: count,
        };

        const dto = plainToInstance(ActionWorkersDto, result);
        validateSync(dto, { whitelist: true, forbidNonWhitelisted: false });
        return dto;
    }
}

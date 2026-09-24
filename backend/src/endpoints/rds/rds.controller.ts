import { ApiOkResponse } from '@/decorators';
import {
    CreateRdsDatasetDto,
    CreateRdsFilterResultDto,
    RdsCleaningSummaryDto,
    RdsDatasetDto,
    RdsDatasetSummaryDto,
    RdsFilterResultDto,
    SaveRdsResultsDto,
} from '@rslstudio/api-dto';
import {
    Body,
    Controller,
    Delete,
    Get,
    Param,
    Post,
} from '@nestjs/common';
import { RdsService } from './rds.service';

@Controller('rds')
export class RdsController {
    constructor(private readonly rdsService: RdsService) {}

    @Post('datasets')
    @ApiOkResponse({
        description: '创建数据集记录',
        type: RdsDatasetDto,
    })
    async createDataset(@Body() dto: CreateRdsDatasetDto): Promise<RdsDatasetDto> {
        return this.rdsService.createDataset(dto);
    }

    @Get('projects/:projectUuid/datasets')
    @ApiOkResponse({
        description: '获取项目下所有数据集摘要',
        type: [RdsDatasetSummaryDto],
    })
    async getDatasetsByProject(
        @Param('projectUuid') projectUuid: string,
    ): Promise<RdsDatasetSummaryDto[]> {
        return this.rdsService.getDatasetsByProject(projectUuid);
    }

    @Get('datasets/:uuid')
    @ApiOkResponse({
        description: '获取数据集详情',
        type: RdsDatasetDto,
    })
    async getDataset(@Param('uuid') uuid: string): Promise<RdsDatasetDto> {
        return this.rdsService.getDataset(uuid);
    }

    @Delete('datasets/:uuid')
    @ApiOkResponse({
        description: '删除数据集',
    })
    async deleteDataset(@Param('uuid') uuid: string): Promise<void> {
        return this.rdsService.deleteDataset(uuid);
    }

    @Post('datasets/:uuid/results')
    @ApiOkResponse({
        description: '保存完整的结构化处理结果',
        type: RdsDatasetDto,
    })
    async saveResults(
        @Param('uuid') uuid: string,
        @Body() dto: SaveRdsResultsDto,
    ): Promise<RdsDatasetDto> {
        return this.rdsService.saveResults(uuid, dto);
    }

    @Get('datasets/:uuid/cleaning-summary')
    @ApiOkResponse({
        description: '获取清洗摘要',
        type: RdsCleaningSummaryDto,
    })
    async getCleaningSummary(
        @Param('uuid') uuid: string,
    ): Promise<RdsCleaningSummaryDto> {
        return this.rdsService.getCleaningSummary(uuid);
    }

    @Post('datasets/:uuid/filter-results')
    @ApiOkResponse({
        description: '保存过滤结果',
        type: [RdsFilterResultDto],
    })
    async saveFilterResults(
        @Param('uuid') uuid: string,
        @Body() results: CreateRdsFilterResultDto[],
    ): Promise<RdsFilterResultDto[]> {
        return this.rdsService.saveFilterResults(uuid, results);
    }

    @Get('datasets/:uuid/filter-results')
    @ApiOkResponse({
        description: '获取过滤结果',
        type: [RdsFilterResultDto],
    })
    async getFilterResults(
        @Param('uuid') uuid: string,
    ): Promise<RdsFilterResultDto[]> {
        return this.rdsService.getFilterResults(uuid);
    }
}

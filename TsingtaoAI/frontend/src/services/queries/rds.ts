import type { RdsDatasetSummaryDto } from '@rslstudio/api-dto/types/rds/rds-dataset.dto';
import type { RdsDatasetDto } from '@rslstudio/api-dto/types/rds/rds-dataset.dto';
import type { RdsCleaningSummaryDto } from '@rslstudio/api-dto/types/rds/rds-cleaning-summary.dto';
import { AxiosResponse } from 'axios';
import axios from 'src/api/axios';

/** 获取项目下所有数据集质检摘要 */
export const getDatasetsByProject = async (
    projectUuid: string,
): Promise<RdsDatasetSummaryDto[]> => {
    const response: AxiosResponse<RdsDatasetSummaryDto[]> =
        await axios.get<RdsDatasetSummaryDto[]>(
            `/rds/projects/${projectUuid}/datasets`,
        );
    return response.data;
};

/** 获取数据集详情 */
export const getRdsDataset = async (
    uuid: string,
): Promise<RdsDatasetDto> => {
    const response: AxiosResponse<RdsDatasetDto> =
        await axios.get<RdsDatasetDto>(`/rds/datasets/${uuid}`);
    return response.data;
};

/** 获取清洗摘要 */
export const getCleaningSummary = async (
    datasetUuid: string,
): Promise<RdsCleaningSummaryDto> => {
    const response: AxiosResponse<RdsCleaningSummaryDto> =
        await axios.get<RdsCleaningSummaryDto>(
            `/rds/datasets/${datasetUuid}/cleaning-summary`,
        );
    return response.data;
};

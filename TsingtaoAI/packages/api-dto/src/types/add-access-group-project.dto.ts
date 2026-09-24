import { AccessGroupRights } from '@rslstudio/shared';
import { ApiProperty } from '@nestjs/swagger';
import { IsEnum } from 'class-validator';

export class AddAccessGroupToProjectDto {
    @IsEnum(AccessGroupRights)
    @ApiProperty({
        description: 'Access Group Rights',
        format: 'AccessGroupRights',
        enum: AccessGroupRights,
    })
    rights!: AccessGroupRights;
}

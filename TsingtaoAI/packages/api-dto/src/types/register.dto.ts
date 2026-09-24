import { ApiProperty } from '@nestjs/swagger';
import { IsEmail, IsString, MaxLength, MinLength } from 'class-validator';

export class RegisterDto {
    @ApiProperty({ example: 'John Doe' })
    @IsString()
    @MinLength(1)
    @MaxLength(100)
    name!: string;

    @ApiProperty({ example: 'user@example.com' })
    @IsEmail()
    email!: string;

    @ApiProperty({ example: 'my-secret-password' })
    @IsString()
    @MinLength(8)
    @MaxLength(128)
    password!: string;
}

import { Injectable, UnauthorizedException } from '@nestjs/common';
import { InjectRepository } from '@nestjs/typeorm';
import { Repository } from 'typeorm';
import * as bcrypt from 'bcrypt';
import { UserEntity } from '@rslstudio/backend-common/entities/user/user.entity';

const SALT_ROUNDS = 12;

@Injectable()
export class LocalAuthService {
    constructor(
        @InjectRepository(UserEntity)
        private userRepository: Repository<UserEntity>,
    ) {}

    /**
     * Validate a user's email and password for local authentication.
     *
     * @param email - The user's email
     * @param password - The user's plain-text password
     * @returns The user entity (without password)
     * @throws UnauthorizedException if credentials are invalid
     */
    async validateUser(
        email: string,
        password: string,
    ): Promise<UserEntity> {
        const user = await this.userRepository.findOne({
            where: { email },
            select: [
                'uuid',
                'email',
                'name',
                'role',
                'avatarUrl',
                'password',
                'hidden',
            ],
            relations: ['memberships'],
        });

        if (!user) {
            throw new UnauthorizedException('邮箱或密码错误');
        }

        // User exists but has no password (OAuth-only account)
        if (!user.password) {
            throw new UnauthorizedException(
                '该账户使用 OAuth 登录，请使用 Google 或 GitHub 登录',
            );
        }

        const isPasswordValid = await bcrypt.compare(password, user.password);
        if (!isPasswordValid) {
            throw new UnauthorizedException('邮箱或密码错误');
        }

        // Strip password before returning
        const { password: _, ...safeUser } = user;
        return safeUser as unknown as UserEntity;
    }

    /**
     * Hash a plain-text password.
     *
     * @param password - The plain-text password to hash
     * @returns The hashed password
     */
    async hashPassword(password: string): Promise<string> {
        return bcrypt.hash(password, SALT_ROUNDS);
    }
}

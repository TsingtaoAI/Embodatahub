import { AuthService } from '@/services/auth.service';
import env from '@rslstudio/backend-common/environment';
import { Providers } from '@rslstudio/shared';
import { Injectable } from '@nestjs/common';
import { PassportStrategy } from '@nestjs/passport';
import e from 'express';
import {
    Strategy as OAuth2Strategy,
    StrategyOptions,
    VerifyCallback,
} from 'passport-oauth2';
import logger from '../../logger';

/**
 *
 * A very basic OAuth2 strategy for local development and testing purposes.
 * Do NOT use this in production!
 *
 */
@Injectable()
export class FakeOauthStrategy extends PassportStrategy(
    OAuth2Strategy,
    Providers.FakeOAuth,
) {
    constructor(private authService: AuthService) {
        super({
            authorizationURL: 'http://localhost:5000/oauth/authorize',
            tokenURL: 'http://localhost:5000/oauth/token',
            clientID: 'some-random-string-it-does-not-matter',
            clientSecret: 'some-random-string-it-does-not-matter',
            callbackURL: `${env.FRONTEND_URL}/auth/fake-oauth/callback`,
            scope: [],
        } as StrategyOptions);
    }

    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    authenticate(request: e.Request, options?: any) {
        // 根据请求的 Host 动态设置 OAuth 重定向 URL，兼容远程域名访问
        const host = request.get('host') || `localhost:${env.FRONTEND_URL?.split(':').pop() || '8003'}`;
        const proto = request.get('x-forwarded-proto') || 'http';
        const baseUrl = `${proto}://${host}`;

        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        (this as any)._oauth2._authorizeUrl = `${baseUrl}/oauth/authorize`;
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        (this as any)._callbackURL = `${baseUrl}/auth/fake-oauth/callback`;

        // eslint-disable-next-line @typescript-eslint/no-unsafe-member-access
        options.state = request.query.state;
        // Pass the user parameter to the OAuth provider for auto-login
        if (request.query.user) {
            // eslint-disable-next-line @typescript-eslint/no-unsafe-member-access
            options.user = request.query.user;
        }
        super.authenticate(request, options);
    }

    async validate(
        accessToken: string,
        _refreshToken: string,
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        _profile: any,
        callback: VerifyCallback,
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
    ): Promise<any> {
        // fetch profile from http://fake-oauth:5000/oauth/profile

        const fetchedProfileResponse = await fetch(
            'http://localhost:5000/oauth/profile',
            {
                headers: {
                    Authorization: `Bearer ${accessToken}`,
                },
            },
        );

        // eslint-disable-next-line @typescript-eslint/no-unsafe-assignment
        const fetchedProfile = await fetchedProfileResponse.json();
        const user =
            await this.authService.validateAndCreateUserByFakeOAuth(
                fetchedProfile,
            );

        // eslint-disable-next-line @typescript-eslint/no-unnecessary-condition
        if (user) {
            logger.debug(`Login successful for ${user.uuid}`);
            callback(null, user);
            return;
        }

        callback(null);
        return;
    }
}

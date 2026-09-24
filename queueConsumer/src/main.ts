// this input must be at the top of the file
import tracer from './tracing';

import { NestFactory } from '@nestjs/core';
import { AppModule } from './app.module';
import logger, { NestLoggerWrapper } from './logger';

async function bootstrap(): Promise<void> {
    tracer.start();
    const app = await NestFactory.create(AppModule, {
        logger: new NestLoggerWrapper(),
    });
    const port = process.env.QUEUE_CONSUMER_PORT || 3001;
    await app.listen(port, '0.0.0.0');
    logger.info(`Application started on port ${port}`);

    if (module.hot) {
        module.hot.accept();
        module.hot.dispose(() => app.close());
    }
}

declare const module: {
    hot?: {
        accept: () => void;
        dispose: (callback: () => Promise<void>) => void;
    };
};

// eslint-disable-next-line unicorn/prefer-top-level-await
bootstrap().catch((error: unknown) => {
    logger.error('Failed to start application');
    logger.error(error);
});

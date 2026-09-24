import { Module } from '@nestjs/common';
import { StreamManagerService } from '../../services/stream-manager.service';
import { StreamController } from './stream.controller';

@Module({
    controllers: [StreamController],
    providers: [StreamManagerService],
    exports: [StreamManagerService],
})
export class StreamModule {}

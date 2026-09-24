import { Readable } from 'node:stream';

export interface FileSourceResult {
    stream: Readable;
    filename: string;
    size?: number;
    mimeType?: string;
}

export interface FileSourceStrategy {
    supports(location: string): boolean;
    fetch(identifier: string): Promise<FileSourceResult>;
}

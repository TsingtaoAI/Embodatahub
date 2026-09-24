import { exec } from 'node:child_process';
import { promisify } from 'node:util';
import logger from '../../logger';
import { traceWrapper } from '../../tracing';

const execPromise = promisify(exec);

export const RosBagConverter = {
    /**
     * Wrapper around the 'mcap' CLI tool.
     * Converts a ROS1 .bag file to a ROS2 .mcap file.
     */
    async convert(inputFile: string, outputFile: string): Promise<void> {
        return traceWrapper(async (): Promise<void> => {
            logger.debug(`Converting ${inputFile} -> ${outputFile}`);

            // You might want to add timeout or max buffer options here for safety
            await execPromise(`mcap convert "${inputFile}" "${outputFile}"`);

            logger.debug(`Conversion successful: ${outputFile}`);
        }, 'RosBagConverter.convert')();
    },
};

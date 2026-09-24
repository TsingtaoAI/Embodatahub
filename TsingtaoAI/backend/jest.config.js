/** @type {import('ts-jest').JestConfigWithTsJest} **/
module.exports = {
    testEnvironment: 'node',
    transform: {
        '^.+\\.[tj]sx?$': [
            'ts-jest',
            {
                tsconfig: 'tsconfig.test.json',
            },
        ],
    },
    moduleNameMapper: {
        '^@/(.*)$': '<rootDir>/src/$1',
        '^@common/(.*)$': '<rootDir>/../common/$1',
        '^@rslstudio/backend-common$':
            '<rootDir>/../packages/backend-common/src/index.ts',
        '^@rslstudio/backend-common/(.*)$':
            '<rootDir>/../packages/backend-common/src/$1',
        '^@backend-common/(.*)$': '<rootDir>/../packages/backend-common/src/$1',
        '^@rslstudio/shared$': '<rootDir>/../packages/shared/src/index.ts',
        '^@rslstudio/shared/(.*)$': '<rootDir>/../packages/shared/src/$1',
        '^@rslstudio/validation$':
            '<rootDir>/../packages/validation/src/index.ts',
        '^@rslstudio/validation/(.*)$':
            '<rootDir>/../packages/validation/src/$1',
        '^@rslstudio/api-dto$': '<rootDir>/../packages/api-dto/src/index.ts',
        '^@rslstudio/api-dto/(.*)$': '<rootDir>/../packages/api-dto/src/$1',
        '^@api-dto/(.*)$': '<rootDir>/../packages/api-dto/src/types/$1',
    },
    preset: 'ts-jest',
    modulePathIgnorePatterns: ['<rootDir>/dist/'],
    transformIgnorePatterns: [],
    reporters: ['<rootDir>/tests/utils/reporter.js'],
};

// set env variables from ../.env
require('dotenv').config({ path: '../.env' });

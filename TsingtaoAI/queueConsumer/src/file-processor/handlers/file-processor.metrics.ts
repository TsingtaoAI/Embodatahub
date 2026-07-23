import { makeGaugeProvider } from '@willsoto/nestjs-prometheus';

const METRIC_NAMES = [
    'backend_online_workers',
    'backend_pending_jobs',
    'backend_active_jobs',
    'backend_completed_jobs',
    'backend_failed_jobs',
] as const;

export const METRIC_PROVIDERS = METRIC_NAMES.map((name) =>
    makeGaugeProvider({
        name,
        help: `Number of ${name.replace('backend_', '').replace('_', ' ')}`,
        labelNames: ['queue'],
    }),
);

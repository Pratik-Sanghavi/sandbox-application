import { NativeConnection, Worker } from "@temporalio/worker";
import * as activities from "./activities";

const temporalAddress = process.env.TEMPORAL_ADDRESS ?? "temporal-frontend.temporal.svc.cluster.local:7233";
const temporalNamespace = process.env.TEMPORAL_NAMESPACE ?? "default";
const taskQueue = process.env.TEMPORAL_TASK_QUEUE ?? "sandbox-hubspot-api-test";

async function run(): Promise<void> {
  const connection = await NativeConnection.connect({ address: temporalAddress });
  const worker = await Worker.create({
    connection,
    namespace: temporalNamespace,
    taskQueue,
    workflowsPath: require.resolve("./workflows"),
    activities,
  });

  console.log(`Temporal worker polling task queue ${taskQueue} in namespace ${temporalNamespace}`);
  await worker.run();
}

run().catch((error: unknown) => {
  console.error("Temporal worker failed", error);
  process.exit(1);
});
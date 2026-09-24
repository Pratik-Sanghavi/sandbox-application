import { proxyActivities } from "@temporalio/workflow";
import type * as activities from "./activities";

const { createContact, listContacts } = proxyActivities<typeof activities>({
  startToCloseTimeout: "30 seconds",
});

export interface HubSpotSandboxResult {
  createdContact: Record<string, unknown>;
  contacts: Record<string, unknown>;
}

export async function createContactThenListContacts(email: string): Promise<HubSpotSandboxResult> {
  const createdContact = await createContact(email);
  const contacts = await listContacts();
  return { createdContact, contacts };
}
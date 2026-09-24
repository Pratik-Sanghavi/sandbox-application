export type HubSpotContact = Record<string, unknown>;

const HUBSPOT_CONTACTS_URL = "https://api.hubapi.com/crm/v3/objects/contacts";

async function hubspotRequest(url: string, init?: RequestInit): Promise<HubSpotContact> {
  const response = await fetch(url, init);
  const body = (await response.json()) as HubSpotContact;
  if (!response.ok) {
    throw new Error(`HubSpot request failed with ${response.status}: ${JSON.stringify(body)}`);
  }
  return body;
}

export async function createContact(email: string): Promise<HubSpotContact> {
  return hubspotRequest(HUBSPOT_CONTACTS_URL, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      properties: {
        email,
        firstname: "Temporal",
        lastname: "Sandbox",
      },
    }),
  });
}

export async function listContacts(): Promise<HubSpotContact> {
  return hubspotRequest(HUBSPOT_CONTACTS_URL);
}
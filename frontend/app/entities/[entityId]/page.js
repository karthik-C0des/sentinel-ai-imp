import EntityDetailWrapper from "@/components/entities/EntityDetailWrapper";

export const metadata = {
  title: 'SentinelAI - Entity Details',
  description: 'Detailed entity information and risk assessment for AML/KYC compliance',
};

export default async function EntityDetailPage({ params }) {
  const { entityId } = await params;

  return <EntityDetailWrapper entityId={entityId} />;
}
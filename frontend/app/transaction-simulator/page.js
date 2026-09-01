import TransactionSimulatorWrapper from "@/components/transactionSimulator/TransactionSimulatorWrapper";

export const metadata = {
  title: 'SentinelAI - Transaction Simulator',
  description: 'Simulate and detect fraudulent transactions with SentinelAI',
};

export default function TransactionSimulatorPage() {
  return <TransactionSimulatorWrapper />;
}
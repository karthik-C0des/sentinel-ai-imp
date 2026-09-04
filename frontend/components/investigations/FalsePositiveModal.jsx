import React, { useState } from 'react';
import Modal from '@leafygreen-ui/modal';
import Button from '@leafygreen-ui/button';
import { Body, Subtitle } from '@leafygreen-ui/typography';
import { Option, Select } from '@leafygreen-ui/select';
import TextArea from '@leafygreen-ui/text-area';
import { palette } from '@/lib/theme';
import { spacing } from '@leafygreen-ui/tokens';

export default function FalsePositiveModal({ open, setOpen, onSubmit, transactionId }) {
  const [reason, setReason] = useState('');
  const [notes, setNotes] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async () => {
    if (!reason) return;
    setIsSubmitting(true);
    await onSubmit(transactionId, reason, notes);
    setIsSubmitting(false);
    setOpen(false);
    setReason('');
    setNotes('');
  };

  return (
    <Modal open={open} setOpen={setOpen} size="small">
      <Subtitle style={{ marginBottom: spacing[3] }}>Mark as False Positive</Subtitle>
      <Body style={{ marginBottom: spacing[3] }}>
        You are about to clear this transaction as a false positive. This will reverse its impact on the customer's risk profile.
      </Body>

      <div style={{ marginBottom: spacing[3] }}>
        <Select
          label="Why is this a false positive?"
          placeholder="Select a reason"
          value={reason}
          onChange={setReason}
          usePortal={false}
        >
          <Option value="customer_traveled">Customer is traveling</Option>
          <Option value="new_device">Legitimate new device</Option>
          <Option value="unusual_but_legit">Unusual but legitimate transaction</Option>
          <Option value="other">Other</Option>
        </Select>
      </div>

      <div style={{ marginBottom: spacing[4] }}>
        <TextArea
          label="Analyst Notes"
          placeholder="Provide additional details..."
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
          rows={4}
        />
      </div>

      <div style={{ display: 'flex', gap: spacing[2], justifyContent: 'flex-end' }}>
        <Button onClick={() => setOpen(false)} variant="default">Cancel</Button>
        <Button 
          onClick={handleSubmit} 
          variant="primary" 
          disabled={!reason || isSubmitting}
          style={{ background: palette.green.dark2, borderColor: palette.green.dark2 }}
        >
          Confirm False Positive
        </Button>
      </div>
    </Modal>
  );
}

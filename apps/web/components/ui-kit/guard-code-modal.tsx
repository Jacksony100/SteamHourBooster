"use client";

import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Modal } from "@/components/ui-kit/modal";

type GuardCodeModalProps = {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  accountLabel: string;
  submitting?: boolean;
  /** Called with the entered Steam Guard code. Parent performs the request + closes. */
  onSubmit: (code: string) => void;
};

/**
 * Accessible (Radix-backed: focus trap, Esc, ARIA) modal that collects a single-use
 * Steam Guard code for starting a REAL owner-operated session.
 */
export function GuardCodeModal({ open, onOpenChange, accountLabel, submitting = false, onSubmit }: GuardCodeModalProps) {
  const [code, setCode] = useState("");

  function submit(e: React.FormEvent) {
    e.preventDefault();
    if (!code.trim()) return;
    onSubmit(code.trim());
  }

  return (
    <Modal
      open={open}
      onOpenChange={(next) => {
        if (!next) setCode("");
        onOpenChange(next);
      }}
      title="Steam Guard code"
      description={`Enter the current Steam Guard code for ${accountLabel} to start a real session. The code is single-use and is never stored.`}
      footer={
        <div className="flex justify-end gap-2">
          <Button variant="ghost" onClick={() => onOpenChange(false)} disabled={submitting}>
            Cancel
          </Button>
          <Button onClick={submit} disabled={submitting || !code.trim()}>
            {submitting ? "Starting..." : "Start session"}
          </Button>
        </div>
      }
    >
      <form onSubmit={submit}>
        <Input
          autoFocus
          value={code}
          onChange={(e) => setCode(e.target.value.toUpperCase())}
          placeholder="XXXXX"
          maxLength={16}
          inputMode="text"
          autoComplete="one-time-code"
          aria-label="Steam Guard code"
          className="text-center tracking-[0.3em]"
        />
      </form>
    </Modal>
  );
}

"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { useLanguage } from "@/components/language-provider";
import { api } from "@/lib/api";
import { SteamLoginButton } from "@/features/auth/steam-login-button";

export function AuthForm({ mode }: { mode: "login" | "register" }) {
  const router = useRouter();
  const { t, language } = useLanguage();
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [resetting, setResetting] = useState(false);
  const isRegister = mode === "register";

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    try {
      await api(`/api/v1/auth/${isRegister ? "register" : "login"}`, {
        method: "POST",
        body: JSON.stringify({ username, email: isRegister ? email || null : undefined, password, accepted_terms: true })
      });
      toast.success(isRegister ? t.auth.formRegisterTitle : t.auth.formLoginTitle);
      router.push("/dashboard");
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Authentication failed");
    }
  }

  async function requestPasswordReset() {
    setResetting(true);
    try {
      await api("/api/v1/auth/password-reset/request", {
        method: "POST",
        body: JSON.stringify({ username })
      });
      toast.success("Recovery request recorded.");
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Recovery request failed");
    } finally {
      setResetting(false);
    }
  }

  return (
    <Card className="w-full max-w-md space-y-5">
      <div>
        <h1 className="text-2xl font-bold">{isRegister ? t.auth.formRegisterTitle : t.auth.formLoginTitle}</h1>
        <p className="mt-2 text-sm text-slate-400">
          {isRegister ? t.auth.formRegisterHelp : t.auth.formLoginHelp}
        </p>
      </div>
      <form className="space-y-4" onSubmit={submit}>
        <label className="grid gap-2 text-sm font-semibold text-slate-300">
          {t.auth.username}
          <Input value={username} onChange={(event) => setUsername(event.target.value)} autoComplete="username" required />
        </label>
        {isRegister && (
          <label className="grid gap-2 text-sm font-semibold text-slate-300">
            Email
            <Input value={email} onChange={(event) => setEmail(event.target.value)} autoComplete="email" placeholder="you@example.com" type="email" />
          </label>
        )}
        <label className="grid gap-2 text-sm font-semibold text-slate-300">
          {t.auth.password}
          <Input
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            type="password"
            autoComplete={isRegister ? "new-password" : "current-password"}
            required
            minLength={8}
          />
        </label>
        {isRegister && (
          <div className="rounded-xl border border-emerald-300/20 bg-emerald-300/10 p-3 text-sm leading-6 text-emerald-100">
            {t.auth.registerNotice}
          </div>
        )}
        <Button className="w-full" type="submit" variant={isRegister ? "success" : "default"}>
          {isRegister ? t.auth.submitRegister : t.auth.submitLogin}
        </Button>
        {!isRegister && (
          <Button className="w-full" disabled={!username || resetting} type="button" variant="ghost" onClick={requestPasswordReset}>
            {resetting ? "Sending..." : "Forgot password"}
          </Button>
        )}
      </form>

      <div className="flex items-center gap-3 text-xs uppercase tracking-wide text-slate-500">
        <span className="h-px flex-1 bg-shb-border" />
        {language === "ru" ? "или" : "or"}
        <span className="h-px flex-1 bg-shb-border" />
      </div>
      <SteamLoginButton className="w-full" />
    </Card>
  );
}

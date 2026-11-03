"use client";

import { useEffect, useRef } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Spinner } from "@/components/ui/spinner";
import { useConfirmEmail } from "../hooks/use-auth-mutations";
import { authErrorMessage } from "../utils/error-message";

/** Opened from the verification letter; confirms the link once on arrival. */
export function VerifyEmailScreen() {
  const token = useSearchParams().get("token");
  const confirmMutation = useConfirmEmail();
  const { mutate } = confirmMutation;
  const sent = useRef(false);

  useEffect(() => {
    // A link is single-use: a second call (Strict Mode) would report it spent.
    if (!token || sent.current) return;
    sent.current = true;
    mutate(token);
  }, [mutate, token]);

  const failed = !token || confirmMutation.isError;
  return (
    <Card className="w-full max-w-sm">
      <CardHeader>
        <CardTitle>Xác minh email</CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col gap-4">
        {confirmMutation.isSuccess && (
          <Alert>
            <AlertDescription>Email của bạn đã được xác minh.</AlertDescription>
          </Alert>
        )}
        {failed && (
          <Alert variant="destructive">
            <AlertDescription>
              {authErrorMessage(confirmMutation.error ?? { code: "invalid_token" })}
            </AlertDescription>
          </Alert>
        )}
        {!failed && !confirmMutation.isSuccess && (
          <div className="flex justify-center" aria-busy="true">
            <Spinner aria-label="Đang xác minh" />
          </div>
        )}
        <Button asChild variant={failed ? "outline" : "default"}>
          <Link href="/">Vào ứng dụng</Link>
        </Button>
      </CardContent>
    </Card>
  );
}

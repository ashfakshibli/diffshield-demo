import { NextResponse } from "next/server";
import { startScan } from "@/lib/analyzer";

export async function POST(request: Request) {
  try {
    const payload = (await request.json()) as {
      repoPath?: string;
      useSample?: boolean;
      notes?: string;
    };
    const result = await startScan(payload);
    return NextResponse.json({ scanId: result.scan_id, repoPath: result.repo_path });
  } catch (error) {
    return NextResponse.json(
      {
        error: error instanceof Error ? error.message : "Failed to start scan"
      },
      { status: 500 }
    );
  }
}


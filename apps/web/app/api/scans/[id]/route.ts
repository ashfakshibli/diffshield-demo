import { NextResponse } from "next/server";
import { getScanBundle } from "@/lib/analyzer";

export async function GET(
  _request: Request,
  context: { params: Promise<{ id: string }> }
) {
  try {
    const { id } = await context.params;
    const bundle = await getScanBundle(id);
    return NextResponse.json(bundle);
  } catch (error) {
    return NextResponse.json(
      {
        error: error instanceof Error ? error.message : "Failed to load scan"
      },
      { status: 500 }
    );
  }
}


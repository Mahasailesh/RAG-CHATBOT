import type { ExtractedDocument } from "@/lib/types";

const MOCK_EXTRACTION = process.env.NEXT_PUBLIC_E2E_MOCK === "true";

type ProgressCallback = (current: number, total: number) => void;

export async function extractPdfText(
  file: File,
  onProgress?: ProgressCallback
): Promise<ExtractedDocument> {
  if (MOCK_EXTRACTION) {
    return {
      documentId: file.name.replace(/\.pdf$/i, ""),
      fileName: file.name,
      pageCount: 1,
      pages: { 1: "Mock document content for audit." }
    };
  }

  const pdfjs = await import("pdfjs-dist");
  const workerSrc = new URL("pdfjs-dist/build/pdf.worker.min.mjs", import.meta.url).toString();
  pdfjs.GlobalWorkerOptions.workerSrc = workerSrc;

  const buffer = await file.arrayBuffer();
  const loadingTask = pdfjs.getDocument({ data: new Uint8Array(buffer) });
  const document = await loadingTask.promise;
  const pages: Record<number, string> = {};

  for (let pageNumber = 1; pageNumber <= document.numPages; pageNumber += 1) {
    const page = await document.getPage(pageNumber);
    const content = await page.getTextContent();
    const text = content.items
      .map((item: any) => (typeof item?.str === "string" ? item.str : ""))
      .filter(Boolean)
      .join(" ")
      .replace(/\s+/g, " ")
      .trim();
    if (text) {
      pages[pageNumber] = text;
    }
    if (onProgress) {
      onProgress(pageNumber, document.numPages);
    }
  }

  if (Object.keys(pages).length === 0) {
    throw new Error("No extractable text found.");
  }

  if (typeof document.cleanup === "function") {
    await document.cleanup();
  }
  if (typeof loadingTask.destroy === "function") {
    await loadingTask.destroy();
  }

  return {
    documentId: file.name.replace(/\.pdf$/i, ""),
    fileName: file.name,
    pageCount: document.numPages,
    pages
  };
}

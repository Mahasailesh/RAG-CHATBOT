import { render, fireEvent, screen, waitFor } from "@testing-library/react";
import { vi } from "vitest";

import { UploadZone } from "@/components/upload-zone";
import { extractPdfText } from "@/lib/pdf";

vi.mock("@/lib/pdf", () => ({
  extractPdfText: vi.fn()
}));

const mockedExtract = vi.mocked(extractPdfText);

describe("UploadZone", () => {
  it("triggers extraction on drag and drop", async () => {
    const onExtracted = vi.fn();
    const onError = vi.fn();

    mockedExtract.mockResolvedValueOnce({
      documentId: "sample",
      fileName: "sample.pdf",
      pageCount: 1,
      pages: { 1: "Mock page" }
    });

    render(
      <UploadZone
        extracted={null}
        onExtracted={onExtracted}
        onError={onError}
        onReset={vi.fn()}
      />
    );

    const dropzone = screen.getByTestId("upload-dropzone");
    const file = new File(["dummy"], "sample.pdf", { type: "application/pdf" });

    fireEvent.drop(dropzone, {
      dataTransfer: { files: [file] }
    });

    await waitFor(() => expect(mockedExtract).toHaveBeenCalledWith(file, expect.any(Function)));
    expect(onExtracted).toHaveBeenCalledWith(
      expect.objectContaining({ fileName: "sample.pdf", pageCount: 1 })
    );
  });
});

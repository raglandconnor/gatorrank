const DEFAULT_FONT = '400 14px Arial';
const TAG_BUFFER_PX = 8;
const SEPARATOR_WIDTH_PX = 22;

let canvasContext: CanvasRenderingContext2D | null = null;

function getCanvasContext(): CanvasRenderingContext2D | null {
  if (typeof document === 'undefined') return null;
  if (canvasContext) return canvasContext;

  const canvas = document.createElement('canvas');
  canvasContext = canvas.getContext('2d');
  return canvasContext;
}

function measureTagWidth(tag: string): number {
  const context = getCanvasContext();
  if (!context) {
    return tag.length * 8 + TAG_BUFFER_PX;
  }

  context.font = DEFAULT_FONT;
  return Math.ceil(context.measureText(tag).width) + TAG_BUFFER_PX;
}

export function fitInlineTags(
  tags: string[],
  containerWidth: number,
  maxRows: number,
): string[] {
  if (!tags.length || containerWidth <= 0 || maxRows <= 0) return [];

  const visible: string[] = [];
  let row = 1;
  let rowWidth = 0;

  for (const tag of tags) {
    const tagWidth = measureTagWidth(tag);
    const additionalWidth =
      rowWidth === 0 ? tagWidth : SEPARATOR_WIDTH_PX + tagWidth;

    if (rowWidth + additionalWidth <= containerWidth) {
      visible.push(tag);
      rowWidth += additionalWidth;
      continue;
    }

    if (row < maxRows && tagWidth <= containerWidth) {
      row += 1;
      rowWidth = tagWidth;
      visible.push(tag);
      continue;
    }

    break;
  }

  return visible;
}

import { useEffect, useRef } from "react";

/**
 * For a horizontally scrollable element: sets `data-more` on it while content
 * is hidden past its right edge, so CSS can fade that edge as a scroll cue.
 */
export function useScrollFade<T extends HTMLElement>() {
  const ref = useRef<T>(null);

  useEffect(() => {
    const element = ref.current;
    if (!element) return;

    const update = () =>
      element.toggleAttribute(
        "data-more",
        element.scrollLeft + element.clientWidth < element.scrollWidth - 1,
      );
    update();

    element.addEventListener("scroll", update, { passive: true });
    // The element can resize, and its content changes as the user types.
    const resize = new ResizeObserver(update);
    resize.observe(element);
    const mutation = new MutationObserver(update);
    mutation.observe(element, {
      childList: true,
      subtree: true,
      characterData: true,
    });
    return () => {
      element.removeEventListener("scroll", update);
      resize.disconnect();
      mutation.disconnect();
    };
  }, []);

  return ref;
}

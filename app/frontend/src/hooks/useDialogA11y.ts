import { useEffect, useRef } from 'react';
import type { RefObject } from 'react';

const FOCUSABLE_SELECTOR = [
    'a[href]',
    'button:not([disabled])',
    'textarea:not([disabled])',
    'input:not([disabled]):not([type="hidden"])',
    'select:not([disabled])',
    '[tabindex]:not([tabindex="-1"])',
].join(',');

function getFocusableElements(container: HTMLElement): HTMLElement[] {
    const all = Array.from(container.querySelectorAll<HTMLElement>(FOCUSABLE_SELECTOR));
    return all.filter((el) => {
        const style = window.getComputedStyle(el);
        if (style.visibility === 'hidden' || style.display === 'none') return false;
        if (el.getAttribute('aria-hidden') === 'true') return false;
        return true;
    });
}

export function useDialogA11y(
    isOpen: boolean,
    containerRef: RefObject<HTMLElement | null>,
    onClose: () => void,
) {
    const previousFocusRef = useRef<HTMLElement | null>(null);

    useEffect(() => {
        if (!isOpen) return;
        const container = containerRef.current;
        if (!container) return;
        const dialog = container;

        previousFocusRef.current = document.activeElement instanceof HTMLElement
            ? document.activeElement
            : null;

        const focusables = getFocusableElements(dialog);
        const first = focusables[0] ?? dialog;
        window.setTimeout(() => first.focus(), 0);

        function onKeyDown(event: KeyboardEvent) {
            if (event.key === 'Escape') {
                event.preventDefault();
                onClose();
                return;
            }
            if (event.key !== 'Tab') return;

            const currentFocusable = getFocusableElements(dialog);
            if (currentFocusable.length === 0) {
                event.preventDefault();
                dialog.focus();
                return;
            }

            const firstEl = currentFocusable[0];
            const lastEl = currentFocusable[currentFocusable.length - 1];
            const active = document.activeElement as HTMLElement | null;

            if (!event.shiftKey && active === lastEl) {
                event.preventDefault();
                firstEl.focus();
            } else if (event.shiftKey && active === firstEl) {
                event.preventDefault();
                lastEl.focus();
            }
        }

        document.addEventListener('keydown', onKeyDown);
        return () => {
            document.removeEventListener('keydown', onKeyDown);
            previousFocusRef.current?.focus();
        };
    }, [isOpen, containerRef, onClose]);
}

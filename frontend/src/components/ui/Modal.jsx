import { useEffect } from 'react';
import { X } from 'lucide-react';
import { AnimatePresence, motion } from 'framer-motion';
import { cn } from '@/lib/utils';

export function Modal({ open, onClose, title, eyebrow, children, footer, size = 'md' }) {
  useEffect(() => {
    if (!open) return;
    const onKey = (e) => e.key === 'Escape' && onClose?.();
    window.addEventListener('keydown', onKey);
    document.body.style.overflow = 'hidden';
    return () => {
      window.removeEventListener('keydown', onKey);
      document.body.style.overflow = '';
    };
  }, [open, onClose]);

  const widths = { sm: 'max-w-md', md: 'max-w-xl', lg: 'max-w-3xl', xl: 'max-w-5xl' };

  return (
    <AnimatePresence>
      {open && (
        <motion.div
          className="fixed inset-0 z-50 flex items-start justify-center p-6 sm:p-12 overflow-y-auto"
          initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
        >
          <motion.div
            className="absolute inset-0 bg-black/70 backdrop-blur-sm"
            onClick={onClose}
          />
          <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 8 }}
            transition={{ duration: 0.18, ease: [0.22, 1, 0.36, 1] }}
            className={cn('relative w-full panel mt-12', widths[size])}
          >
            <div className="flex items-start justify-between p-5 border-b border-line">
              <div>
                {eyebrow && <p className="eyebrow mb-2">{eyebrow}</p>}
                <h2 className="font-display text-2xl text-bone tracking-tight" style={{ fontVariationSettings: "'opsz' 72" }}>
                  {title}
                </h2>
              </div>
              <button onClick={onClose} className="p-1.5 -m-1.5 text-dim hover:text-bone">
                <X className="w-4 h-4" />
              </button>
            </div>
            <div className="p-5">{children}</div>
            {footer && <div className="px-5 py-4 border-t border-line bg-ink-100">{footer}</div>}
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}

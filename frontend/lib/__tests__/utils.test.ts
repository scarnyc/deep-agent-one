/**
 * Unit Tests for cn() Utility (Phase 0)
 *
 * Tests Tailwind CSS class merging functionality with clsx and tailwind-merge.
 * Ensures proper handling of conditional classes, conflicts, and edge cases.
 *
 * Coverage target: 95%+
 * Test count: 12+ tests
 */

import { cn } from '../utils';

describe('cn utility', () => {
  describe('Basic functionality', () => {
    it('should merge classes correctly', () => {
      // Arrange
      const classes = ['px-4', 'py-2', 'bg-blue-500'];

      // Act
      const result = cn(...classes);

      // Assert
      expect(result).toBe('px-4 py-2 bg-blue-500');
    });

    it('should handle single class string', () => {
      // Arrange
      const className = 'text-center';

      // Act
      const result = cn(className);

      // Assert
      expect(result).toBe('text-center');
    });

    it('should handle multiple class strings', () => {
      // Arrange
      const class1 = 'flex items-center';
      const class2 = 'justify-between';
      const class3 = 'p-4';

      // Act
      const result = cn(class1, class2, class3);

      // Assert
      expect(result).toBe('flex items-center justify-between p-4');
    });
  });

  describe('Conflicting Tailwind classes', () => {
    it('should handle conflicting padding classes (last wins)', () => {
      // Arrange & Act
      const result = cn('px-4', 'px-2');

      // Assert
      expect(result).toBe('px-2');
    });

    it('should handle conflicting text color classes (last wins)', () => {
      // Arrange & Act
      const result = cn('text-red-500', 'text-blue-500');

      // Assert
      expect(result).toBe('text-blue-500');
    });

    it('should handle conflicting background classes (last wins)', () => {
      // Arrange & Act
      const result = cn('bg-gray-100', 'bg-white', 'bg-blue-500');

      // Assert
      expect(result).toBe('bg-blue-500');
    });

    it('should handle conflicting margin classes (last wins)', () => {
      // Arrange & Act
      const result = cn('mt-2', 'mt-4', 'mt-8');

      // Assert
      expect(result).toBe('mt-8');
    });

    it('should preserve non-conflicting classes while resolving conflicts', () => {
      // Arrange & Act
      const result = cn('px-4 py-2 bg-blue-500', 'px-2 text-white');

      // Assert
      expect(result).toBe('py-2 bg-blue-500 px-2 text-white');
    });
  });

  describe('Conditional classes (object syntax)', () => {
    it('should include classes when condition is true', () => {
      // Arrange
      const isActive = true;
      const isDisabled = false;

      // Act
      const result = cn('base-class', {
        'active-class': isActive,
        'disabled-class': isDisabled,
      });

      // Assert
      expect(result).toContain('base-class');
      expect(result).toContain('active-class');
      expect(result).not.toContain('disabled-class');
    });

    it('should handle all false conditions', () => {
      // Arrange
      const result = cn('base-class', {
        'class-1': false,
        'class-2': false,
        'class-3': false,
      });

      // Assert
      expect(result).toBe('base-class');
    });

    it('should handle all true conditions', () => {
      // Arrange
      const result = cn({
        'class-1': true,
        'class-2': true,
        'class-3': true,
      });

      // Assert
      expect(result).toContain('class-1');
      expect(result).toContain('class-2');
      expect(result).toContain('class-3');
    });

    it('should handle complex conditional logic', () => {
      // Arrange
      const isPrimary = true;
      const isLarge = false;
      const isDisabled = false;

      // Act
      const result = cn('btn', {
        'btn-primary': isPrimary,
        'btn-large': isLarge,
        'btn-disabled': isDisabled,
        'btn-enabled': !isDisabled,
      });

      // Assert
      expect(result).toContain('btn');
      expect(result).toContain('btn-primary');
      expect(result).toContain('btn-enabled');
      expect(result).not.toContain('btn-large');
      expect(result).not.toContain('btn-disabled');
    });
  });

  describe('Array inputs', () => {
    it('should handle arrays of classes', () => {
      // Arrange
      const classes = ['flex', 'items-center', 'justify-center'];

      // Act
      const result = cn(classes);

      // Assert
      expect(result).toBe('flex items-center justify-center');
    });

    it('should handle nested arrays', () => {
      // Arrange
      const baseClasses = ['flex', 'items-center'];
      const spacingClasses = ['p-4', 'gap-2'];

      // Act
      const result = cn([baseClasses, spacingClasses]);

      // Assert
      expect(result).toContain('flex');
      expect(result).toContain('items-center');
      expect(result).toContain('p-4');
      expect(result).toContain('gap-2');
    });

    it('should handle mixed arrays and strings', () => {
      // Arrange
      const classes = ['flex', 'items-center'];
      const additional = 'p-4';

      // Act
      const result = cn(classes, additional, 'bg-white');

      // Assert
      expect(result).toBe('flex items-center p-4 bg-white');
    });
  });

  describe('Edge cases', () => {
    it('should handle undefined values', () => {
      // Arrange & Act
      const result = cn('base-class', undefined, 'other-class');

      // Assert
      expect(result).toBe('base-class other-class');
    });

    it('should handle null values', () => {
      // Arrange & Act
      const result = cn('base-class', null, 'other-class');

      // Assert
      expect(result).toBe('base-class other-class');
    });

    it('should handle empty strings', () => {
      // Arrange & Act
      const result = cn('base-class', '', 'other-class');

      // Assert
      expect(result).toBe('base-class other-class');
    });

    it('should handle no arguments', () => {
      // Arrange & Act
      const result = cn();

      // Assert
      expect(result).toBe('');
    });

    it('should handle only falsy values', () => {
      // Arrange & Act
      const result = cn(undefined, null, '', false);

      // Assert
      expect(result).toBe('');
    });
  });

  describe('Mixed inputs', () => {
    it('should handle strings, objects, and arrays together', () => {
      // Arrange
      const isActive = true;
      const isDisabled = false;

      // Act
      const result = cn(
        'base-class',
        ['flex', 'items-center'],
        {
          'active': isActive,
          'disabled': isDisabled,
        },
        'p-4'
      );

      // Assert
      expect(result).toContain('base-class');
      expect(result).toContain('flex');
      expect(result).toContain('items-center');
      expect(result).toContain('active');
      expect(result).toContain('p-4');
      expect(result).not.toContain('disabled');
    });

    it('should handle complex real-world example', () => {
      // Arrange
      const variant = 'primary';
      const size = 'large';
      const isDisabled = false;
      const isLoading = true;

      // Act
      const result = cn(
        'btn',
        'transition-colors',
        {
          'btn-primary': variant === 'primary',
          'btn-secondary': variant === 'secondary',
          'btn-sm': size === 'small',
          'btn-lg': size === 'large',
          'opacity-50 cursor-not-allowed': isDisabled,
          'cursor-wait': isLoading,
        },
        isLoading && 'animate-pulse'
      );

      // Assert
      expect(result).toContain('btn');
      expect(result).toContain('transition-colors');
      expect(result).toContain('btn-primary');
      expect(result).toContain('btn-lg');
      expect(result).toContain('cursor-wait');
      expect(result).toContain('animate-pulse');
      expect(result).not.toContain('btn-secondary');
      expect(result).not.toContain('btn-sm');
      expect(result).not.toContain('opacity-50');
    });

    it('should handle whitespace and duplicate classes', () => {
      // Arrange & Act
      const result = cn(
        'flex   items-center',
        'flex',
        '  justify-center  ',
        'items-center'
      );

      // Assert
      // Duplicates should be merged, order may vary but all classes present
      expect(result).toContain('flex');
      expect(result).toContain('items-center');
      expect(result).toContain('justify-center');
      // Verify no duplicates by checking split length
      const classes = result.split(' ');
      const uniqueClasses = [...new Set(classes)];
      expect(classes).toHaveLength(uniqueClasses.length);
    });
  });

  describe('Tailwind-specific edge cases', () => {
    it('should handle responsive modifiers correctly', () => {
      // Arrange & Act
      const result = cn('hidden', 'md:block', 'lg:flex');

      // Assert
      expect(result).toBe('hidden md:block lg:flex');
    });

    it('should handle state modifiers correctly', () => {
      // Arrange & Act
      const result = cn('bg-blue-500', 'hover:bg-blue-600', 'active:bg-blue-700');

      // Assert
      expect(result).toBe('bg-blue-500 hover:bg-blue-600 active:bg-blue-700');
    });

    it('should handle arbitrary values', () => {
      // Arrange & Act
      const result = cn('p-4', 'p-[13px]');

      // Assert
      expect(result).toBe('p-[13px]');
    });

    it('should handle dark mode classes', () => {
      // Arrange & Act
      const result = cn('bg-white', 'dark:bg-gray-900');

      // Assert
      expect(result).toBe('bg-white dark:bg-gray-900');
    });
  });
});

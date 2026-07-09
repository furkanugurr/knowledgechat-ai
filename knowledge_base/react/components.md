# React Components

## Component Basics

A React component is a reusable function that describes part of a user
interface. Components receive inputs called props and return JSX. JSX combines
HTML-like markup with JavaScript expressions.

```tsx
interface GreetingProps {
  name: string;
}

export function Greeting({ name }: GreetingProps) {
  return <p>Hello, {name}!</p>;
}
```

The parent supplies a `name`, and the component renders the corresponding
message. Props should be treated as read-only values.

## State and Composition

State stores information that can change while a component is mounted. Updating
state asks React to render the affected interface again. State should remain
close to the components that need it unless multiple parts of the interface
must share the same value.

Composition builds interfaces by nesting small components:

```tsx
function Page() {
  return (
    <main>
      <Greeting name="Ada" />
    </main>
  );
}
```

Focused components are easier to understand, test, and reuse. A component
should not be split merely to reduce line count; separation is most useful when
a piece has a clear responsibility or reusable interface.

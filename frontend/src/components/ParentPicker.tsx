import { Button, defaultOptionsFilter, Modal, Select, type ComboboxItem, type OptionsFilter } from '@mantine/core';
import { notifications } from '@mantine/notifications';
import { useState } from 'react';

import { useCreateParent } from '../api/parents';
import type { Parent, ParentCreate } from '../api/types';
import { ParentForm } from './ParentForm';
import { PasswordReveal } from './PasswordModal';

const NEW_PARENT = '__new__';
const NEW_PARENT_OPTION: ComboboxItem = { value: NEW_PARENT, label: '+ Добавить нового' };

const filterKeepingNewOption: OptionsFilter = (input) => [
  ...defaultOptionsFilter({
    ...input,
    options: input.options.filter((item) => !('value' in item) || item.value !== NEW_PARENT),
  }),
  NEW_PARENT_OPTION,
];

interface Props {
  parents: Parent[];
  value: string | null;
  onChange: (value: string | null) => void;
}

export function ParentPicker({ parents, value, onChange }: Props) {
  const [open, setOpen] = useState(false);
  const [created, setCreated] = useState<{ parent: Parent; password: string } | null>(null);
  const create = useCreateParent();

  const createdNotYetListed = created && !parents.some((p) => p.id === created.parent.id);
  const known = createdNotYetListed ? [...parents, created.parent] : parents;
  const data: ComboboxItem[] = [
    ...known
      .filter((p) => p.is_active || String(p.id) === value)
      .map((p) => ({ value: String(p.id), label: p.full_name })),
    NEW_PARENT_OPTION,
  ];

  const select = (next: string | null) => {
    if (next === NEW_PARENT) {
      setCreated(null);
      setOpen(true);
      return;
    }
    onChange(next);
  };

  const submit = (form: ParentCreate) =>
    create.mutate(form, {
      onSuccess: (result) => {
        setCreated(result);
        onChange(String(result.parent.id));
      },
      onError: (error) => notifications.show({ color: 'red', message: error.message }),
    });

  const close = () => setOpen(false);
  const showingPassword = open && created !== null;

  return (
    <>
      <Select
        label="Родитель"
        data={data}
        value={value}
        onChange={select}
        filter={filterKeepingNewOption}
        searchable
        required
      />
      <Modal
        opened={open}
        onClose={close}
        returnFocus={false}
        title={showingPassword ? `Пароль для ${created.parent.full_name}` : 'Новый родитель'}
      >
        {showingPassword ? (
          <PasswordReveal password={created.password}>
            <Button variant="default" onClick={close}>
              Готово
            </Button>
          </PasswordReveal>
        ) : (
          <ParentForm onSubmit={(form) => submit(form as ParentCreate)} busy={create.isPending} />
        )}
      </Modal>
    </>
  );
}

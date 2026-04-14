'use client';

import { useEffect, useMemo, useRef, useState } from 'react';
import {
  Box,
  Flex,
  HStack,
  VStack,
  Text,
  Button,
  Input,
  Textarea,
  Wrap,
  Spinner,
} from '@chakra-ui/react';
import { LuPlus, LuX, LuGlobe, LuGithub, LuPlay, LuTag } from 'react-icons/lu';
import { listCategories, listTags, listTechStacks } from '@/lib/api/taxonomy';
import type {
  ProjectMemberInfo,
  ProjectMemberWritableRole,
  TaxonomyTerm,
} from '@/lib/api/types/project';
import { toast } from '@/lib/ui/toast';

const PROJECT_NAME_MAX = 50;
const SHORT_DESCRIPTION_MAX = 280;
const FULL_DESCRIPTION_MAX = 5000;
const URL_MAX = 2048;
const CATEGORY_LIMIT = 3;
const TAG_LIMIT = 10;
const TECH_STACK_LIMIT = 15;

const inputBase = {
  border: '1px solid',
  borderColor: 'gray.300',
  borderRadius: '10px',
  px: '12px',
  bg: 'white',
  fontSize: 'sm',
  color: 'gray.900',
  w: '100%',
  outline: 'none',
  _focus: { borderColor: 'orange.400' },
} as const;

function isValidHttpUrl(s: string): boolean {
  const trimmed = s.trim();
  if (!trimmed) return false;
  try {
    const u = new URL(trimmed);
    return u.protocol === 'http:' || u.protocol === 'https:';
  } catch {
    return false;
  }
}

function isValidGithubUrl(s: string): boolean {
  if (!isValidHttpUrl(s)) return false;
  try {
    const u = new URL(s.trim());
    const host = u.hostname.toLowerCase();
    return host === 'github.com' || host === 'www.github.com';
  } catch {
    return false;
  }
}

function isValidUflEmail(s: string): boolean {
  const trimmed = s.trim().toLowerCase();
  if (!trimmed.endsWith('@ufl.edu')) return false;
  const local = trimmed.slice(0, -'@ufl.edu'.length);
  return local.length > 0 && !local.includes('@');
}

function FieldLabel({ children }: { children: React.ReactNode }) {
  return (
    <Text fontSize="sm" color="gray.500" lineHeight="24px">
      {children}
    </Text>
  );
}

function normalizeTermName(value: string): string {
  return value.trim().toLowerCase();
}

function containsControlChars(value: string): boolean {
  return /[\u0000-\u001F\u007F-\u009F]/.test(value);
}

interface ProjectTermFieldProps {
  title: string;
  singularLabel: string;
  placeholder: string;
  helperText: string;
  values: string[];
  limit: number;
  loadTerms: () => Promise<TaxonomyTerm[]>;
  loadingText: string;
  loadErrorText: string;
  onChange: (nextValues: string[]) => void;
}

function ProjectTermField({
  title,
  singularLabel,
  placeholder,
  helperText,
  values,
  limit,
  loadTerms,
  loadingText,
  loadErrorText,
  onChange,
}: ProjectTermFieldProps) {
  const [inputValue, setInputValue] = useState('');
  const [availableTerms, setAvailableTerms] = useState<TaxonomyTerm[]>([]);
  const [isLoadingTerms, setIsLoadingTerms] = useState(true);
  const [loadTermsError, setLoadTermsError] = useState<string | null>(null);
  const [isFocused, setIsFocused] = useState(false);

  useEffect(() => {
    let cancelled = false;

    async function fetchTerms() {
      try {
        setIsLoadingTerms(true);
        const terms = await loadTerms();
        if (cancelled) return;
        setAvailableTerms(terms);
        setLoadTermsError(null);
      } catch (error) {
        if (cancelled) return;
        setLoadTermsError(
          error instanceof Error ? error.message : loadErrorText,
        );
      } finally {
        if (!cancelled) {
          setIsLoadingTerms(false);
        }
      }
    }

    void fetchTerms();

    return () => {
      cancelled = true;
    };
  }, [loadErrorText, loadTerms]);

  const normalizedInput = inputValue.trim().toLowerCase();
  const filteredSuggestions = useMemo(() => {
    if (!isFocused) return [];

    const unselectedTerms = availableTerms.filter(
      (term) =>
        !values.some(
          (selected) =>
            normalizeTermName(selected) === normalizeTermName(term.name),
        ),
    );

    if (!normalizedInput) {
      return unselectedTerms.slice(0, 8);
    }

    return unselectedTerms
      .filter((term) => term.name.toLowerCase().includes(normalizedInput))
      .slice(0, 8);
  }, [availableTerms, isFocused, normalizedInput, values]);

  const addValue = (rawValue: string) => {
    const trimmed = rawValue.trim();
    if (!trimmed) return;

    if (
      values.some(
        (existingValue) =>
          normalizeTermName(existingValue) === normalizeTermName(trimmed),
      )
    ) {
      toast.error({
        title: `Duplicate ${singularLabel}`,
        description: `That ${singularLabel} has already been added to this project.`,
      });
      return;
    }

    if (values.length >= limit) {
      toast.error({
        title: `${title} limit reached`,
        description: `You can add up to ${limit} ${title.toLowerCase()} to a project.`,
      });
      return;
    }

    if (trimmed.length < 2 || trimmed.length > 64) {
      toast.error({
        title: `Invalid ${singularLabel}`,
        description: `${title} must be between 2 and 64 characters long.`,
      });
      return;
    }

    if (containsControlChars(trimmed)) {
      toast.error({
        title: `Invalid ${singularLabel}`,
        description: `${title} cannot include control characters.`,
      });
      return;
    }

    onChange([...values, trimmed]);
    setInputValue('');
  };

  const handleAddValue = () => {
    const trimmed = inputValue.trim();
    if (!trimmed) return;

    if (filteredSuggestions.length > 0) {
      addValue(filteredSuggestions[0].name);
      return;
    }

    addValue(trimmed);
  };

  return (
    <Box
      bg="gray.100"
      borderRadius="13px"
      p={{ base: '16px', md: '24px' }}
      w="100%"
    >
      <VStack align="start" gap="12px" w="100%">
        <Text
          fontSize="md"
          fontWeight="bold"
          color="gray.900"
          lineHeight="30px"
        >
          {title}
        </Text>
        <FieldLabel>{helperText}</FieldLabel>

        <HStack gap="8px" w="100%">
          <Input
            value={inputValue}
            onFocus={() => setIsFocused(true)}
            onBlur={() => {
              setTimeout(() => setIsFocused(false), 120);
            }}
            onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
              setInputValue(e.target.value)
            }
            onKeyDown={(e: React.KeyboardEvent) => {
              if (e.key === 'Enter') {
                e.preventDefault();
                handleAddValue();
              }
            }}
            placeholder={placeholder}
            {...inputBase}
            h="40px"
            flex={1}
          />
          <Button
            type="button"
            aria-label={`Add ${singularLabel}`}
            bg="orange.400"
            color="white"
            borderRadius="10px"
            h="40px"
            px="10px"
            _hover={{ bg: 'orange.500' }}
            onClick={handleAddValue}
          >
            <LuPlus size={16} />
          </Button>
        </HStack>

        {isLoadingTerms ? (
          <HStack gap="8px">
            <Spinner size="sm" color="orange.400" />
            <Text fontSize="sm" color="gray.500">
              {loadingText}
            </Text>
          </HStack>
        ) : loadTermsError ? (
          <Text fontSize="sm" color="orange.600">
            {loadTermsError} You can still add your own {title.toLowerCase()}{' '}
            manually.
          </Text>
        ) : isFocused ? (
          <VStack align="start" gap="8px" w="100%">
            {normalizedInput && filteredSuggestions.length > 0 ? (
              <Text fontSize="xs" color="gray.500">
                Press Enter to use &quot;{filteredSuggestions[0].name}&quot;.
              </Text>
            ) : null}
            {filteredSuggestions.length > 0 ? (
              <Wrap gap="8px">
                {filteredSuggestions.map((term) => (
                  <Button
                    key={term.id}
                    type="button"
                    size="sm"
                    variant="outline"
                    borderColor="orange.200"
                    bg="white"
                    color="gray.700"
                    _hover={{ bg: 'orange.50' }}
                    onMouseDown={(event) => event.preventDefault()}
                    onClick={() => addValue(term.name)}
                  >
                    <HStack gap="6px">
                      <LuTag size={13} />
                      <Text>{term.name}</Text>
                    </HStack>
                  </Button>
                ))}
              </Wrap>
            ) : null}
            {normalizedInput ? (
              <Button
                type="button"
                size="sm"
                variant="outline"
                borderColor="gray.300"
                bg="white"
                color="gray.700"
                _hover={{ bg: 'gray.50' }}
                onMouseDown={(event) => event.preventDefault()}
                onClick={() => addValue(inputValue)}
              >
                <HStack gap="6px">
                  <LuPlus size={13} />
                  <Text>Create &quot;{inputValue.trim()}&quot;</Text>
                </HStack>
              </Button>
            ) : null}
          </VStack>
        ) : null}

        {values.length > 0 && (
          <Wrap gap="8px">
            {values.map((value, index) => (
              <HStack
                key={`${value}-${index}`}
                gap="4px"
                bg="white"
                border="1px solid"
                borderColor="orange.200"
                borderRadius="10px"
                px="10px"
                py="4px"
              >
                <Text fontSize="sm" color="gray.700" lineHeight="20px">
                  {value}
                </Text>
                <Button
                  type="button"
                  aria-label={`Remove ${value}`}
                  variant="ghost"
                  size="xs"
                  minW="auto"
                  h="auto"
                  p={0}
                  onClick={() =>
                    onChange(
                      values.filter((_, valueIndex) => valueIndex !== index),
                    )
                  }
                >
                  <LuX size={12} />
                </Button>
              </HStack>
            ))}
          </Wrap>
        )}
      </VStack>
    </Box>
  );
}

function MemberPills({
  members,
  pendingMembers,
  onRemoveMember,
  onUpdateMemberRole,
  onUpdatePendingMemberRole,
  pendingRoleUpdates,
  isBusy,
}: {
  members: ProjectMemberInfo[];
  pendingMembers: PendingProjectMember[];
  onRemoveMember: (idOrEmail: string) => void;
  onUpdateMemberRole: (userId: string, role: ProjectMemberWritableRole) => void;
  onUpdatePendingMemberRole: (
    email: string,
    role: ProjectMemberWritableRole,
  ) => void;
  pendingRoleUpdates: Set<string>;
  isBusy: boolean;
}) {
  if (members.length === 0 && pendingMembers.length === 0) return null;

  return (
    <Wrap gap="8px">
      {members.map((member) => (
        <HStack
          key={member.user_id}
          gap="4px"
          px="10px"
          py="4px"
          borderRadius="10px"
          bg="white"
          border="1px solid"
          borderColor="gray.300"
        >
          <Text fontSize="sm" color="gray.700" lineHeight="20px">
            {member.full_name ?? member.username}
          </Text>
          {member.role === 'owner' ? (
            <Text
              fontSize="xs"
              color="gray.500"
              lineHeight="16px"
              textTransform="capitalize"
            >
              owner
            </Text>
          ) : (
            <select
              aria-label={`Role for ${member.full_name ?? member.username}`}
              value={member.role}
              disabled={isBusy || pendingRoleUpdates.has(member.user_id)}
              onChange={(e: React.ChangeEvent<HTMLSelectElement>) =>
                onUpdateMemberRole(
                  member.user_id,
                  e.target.value as ProjectMemberWritableRole,
                )
              }
              style={{
                width: '132px',
                height: '26px',
                fontSize: '12px',
                background: 'white',
                border: '1px solid var(--chakra-colors-gray-300)',
                borderRadius: '8px',
                paddingInline: '8px',
              }}
            >
              <option value="contributor">Contributor</option>
              <option value="maintainer">Maintainer</option>
            </select>
          )}
          {member.role !== 'owner' && (
            <Button
              type="button"
              aria-label={`Remove ${member.full_name ?? 'member'}`}
              variant="ghost"
              size="xs"
              minW="auto"
              h="auto"
              p={0}
              disabled={isBusy}
              onClick={() => onRemoveMember(member.user_id)}
            >
              <LuX size={12} />
            </Button>
          )}
        </HStack>
      ))}

      {pendingMembers.map((pendingMember) => (
        <HStack
          key={pendingMember.email}
          gap="4px"
          px="10px"
          py="4px"
          borderRadius="10px"
          bg="white"
          border="1px solid"
          borderColor="gray.300"
        >
          <Text fontSize="sm" color="gray.700" lineHeight="20px">
            {pendingMember.email}
          </Text>
          <select
            aria-label={`Role for ${pendingMember.email}`}
            value={pendingMember.role}
            disabled={isBusy}
            onChange={(e: React.ChangeEvent<HTMLSelectElement>) =>
              onUpdatePendingMemberRole(
                pendingMember.email,
                e.target.value as ProjectMemberWritableRole,
              )
            }
            style={{
              width: '132px',
              height: '26px',
              fontSize: '12px',
              background: 'white',
              border: '1px solid var(--chakra-colors-gray-300)',
              borderRadius: '8px',
              paddingInline: '8px',
            }}
          >
            <option value="contributor">Contributor</option>
            <option value="maintainer">Maintainer</option>
          </select>
          <Button
            type="button"
            aria-label={`Remove ${pendingMember.email}`}
            variant="ghost"
            size="xs"
            minW="auto"
            h="auto"
            p={0}
            disabled={isBusy}
            onClick={() => onRemoveMember(pendingMember.email)}
          >
            <LuX size={12} />
          </Button>
        </HStack>
      ))}
    </Wrap>
  );
}

export type ProjectFormMode = 'create' | 'edit';

export interface ProjectFormValues {
  title: string;
  shortDescription: string;
  fullDescription: string;
  imageUrl?: string | null;
  categories: string[];
  tags: string[];
  techStack: string[];
  websiteUrl: string;
  githubUrl: string;
  demoVideoUrl: string;
}

export interface ProjectPayload {
  title: string;
  short_description: string;
  long_description?: string | null;
  demo_url?: string | null;
  github_url?: string | null;
  video_url?: string | null;
  categories?: string[];
  tags?: string[];
  tech_stack?: string[];
}

export interface PendingProjectMember {
  email: string;
  role: ProjectMemberWritableRole;
}

interface ProjectFormProps {
  mode: ProjectFormMode;
  initialValues: ProjectFormValues;
  onSubmit: (payload: ProjectPayload, values: ProjectFormValues) => void;
  onValidityChange?: (isDisabled: boolean) => void;
  publishChecked: boolean;
  onPublishCheckedChange: (checked: boolean) => void;
  members?: ProjectMemberInfo[];
  pendingMembers?: PendingProjectMember[];
  pendingMemberEmails?: string[];
  onAddMember: (
    email: string,
    role?: ProjectMemberWritableRole,
  ) => Promise<{ ok: true } | { ok: false; message: string }>;
  onRemoveMember: (
    idOrEmail: string,
  ) => Promise<{ ok: true } | { ok: false; message: string }>;
  onUpdateMemberRole?: (
    userId: string,
    role: ProjectMemberWritableRole,
  ) => Promise<{ ok: true } | { ok: false; message: string }>;
  onUpdatePendingMemberRole?: (
    email: string,
    role: ProjectMemberWritableRole,
  ) => void;
  isBusy?: boolean;
}

export function ProjectForm({
  mode,
  initialValues,
  onSubmit,
  onValidityChange,
  publishChecked,
  onPublishCheckedChange,
  members = [],
  pendingMembers = [],
  pendingMemberEmails = [],
  onAddMember,
  onRemoveMember,
  onUpdateMemberRole,
  onUpdatePendingMemberRole,
  isBusy = false,
}: ProjectFormProps) {
  const [projectName, setProjectName] = useState(initialValues.title);
  const [shortDescription, setShortDescription] = useState(
    initialValues.shortDescription,
  );
  const [fullDescription, setFullDescription] = useState(
    initialValues.fullDescription,
  );
  const [categories, setCategories] = useState<string[]>(
    initialValues.categories,
  );
  const [tags, setTags] = useState<string[]>(initialValues.tags);
  const [techStack, setTechStack] = useState<string[]>(initialValues.techStack);

  const [memberInput, setMemberInput] = useState('');
  const [memberSubmitting, setMemberSubmitting] = useState(false);
  const [pendingRoleUpdates, setPendingRoleUpdates] = useState<Set<string>>(
    () => new Set(),
  );
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [websiteUrl, setWebsiteUrl] = useState(initialValues.websiteUrl);
  const [githubUrl, setGithubUrl] = useState(initialValues.githubUrl);
  const [demoVideoUrl, setDemoVideoUrl] = useState(initialValues.demoVideoUrl);

  const [errors, setErrors] = useState<{
    projectName?: string;
    shortDescription?: string;
    fullDescription?: string;
    websiteUrl?: string;
    githubUrl?: string;
    demoVideoUrl?: string;
    urls?: string;
  }>({});

  useEffect(() => {
    setProjectName(initialValues.title);
    setShortDescription(initialValues.shortDescription);
    setFullDescription(initialValues.fullDescription);
    setCategories(initialValues.categories);
    setTags(initialValues.tags);
    setTechStack(initialValues.techStack);
    setWebsiteUrl(initialValues.websiteUrl);
    setGithubUrl(initialValues.githubUrl);
    setDemoVideoUrl(initialValues.demoVideoUrl);
  }, [initialValues]);

  const normalizedPendingMembers = useMemo<PendingProjectMember[]>(
    () =>
      pendingMembers.length > 0
        ? pendingMembers
        : pendingMemberEmails.map((email) => ({
            email,
            role: 'contributor',
          })),
    [pendingMemberEmails, pendingMembers],
  );

  const trimmedWebsite = websiteUrl.trim();
  const trimmedGithub = githubUrl.trim();
  const trimmedDemo = demoVideoUrl.trim();
  const hasAtLeastOneUrl = Boolean(
    trimmedWebsite || trimmedGithub || trimmedDemo,
  );

  const isSubmitDisabled =
    !projectName.trim() || !shortDescription.trim() || !hasAtLeastOneUrl;

  useEffect(() => {
    onValidityChange?.(isSubmitDisabled);
  }, [isSubmitDisabled, onValidityChange]);

  const handleAddMember = async () => {
    const normalized = memberInput.trim().toLowerCase();
    if (!normalized) return;

    if (!isValidUflEmail(normalized)) {
      toast.error({
        title: 'Invalid email',
        description: 'Team members must use a valid @ufl.edu email address.',
      });
      return;
    }

    setMemberSubmitting(true);
    try {
      const result = await onAddMember(normalized, 'contributor');

      if (!result.ok) {
        toast.error({
          title: 'Could not add member',
          description: result.message,
        });
        return;
      }

      setMemberInput('');
    } catch {
      toast.error({
        title: 'Could not add member',
        description: 'Please try again.',
      });
    } finally {
      setMemberSubmitting(false);
    }
  };

  const handleUpdateMemberRole = async (
    userId: string,
    role: ProjectMemberWritableRole,
  ) => {
    const currentMember = members.find((member) => member.user_id === userId);
    if (!currentMember || currentMember.role === role) return;

    if (!onUpdateMemberRole) return;

    setPendingRoleUpdates((prev) => {
      const next = new Set(prev);
      next.add(userId);
      return next;
    });

    try {
      const result = await onUpdateMemberRole(userId, role);
      if (!result.ok) {
        toast.error({
          title: 'Could not update member role',
          description: result.message,
        });
      }
    } catch {
      toast.error({
        title: 'Could not update member role',
        description: 'Please try again.',
      });
    } finally {
      setPendingRoleUpdates((prev) => {
        const next = new Set(prev);
        next.delete(userId);
        return next;
      });
    }
  };

  const handleUpdatePendingMemberRole = (
    email: string,
    role: ProjectMemberWritableRole,
  ) => {
    onUpdatePendingMemberRole?.(email, role);
  };

  const handleRemoveMember = async (idOrEmail: string) => {
    try {
      const result = await onRemoveMember(idOrEmail);
      if (!result.ok) {
        toast.error({
          title: 'Could not remove member',
          description: result.message,
        });
      }
    } catch {
      toast.error({
        title: 'Could not remove member',
        description: 'Please try again.',
      });
    }
  };

  const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (isSubmitDisabled) return;

    const nextErrors: typeof errors = {};

    const trimmedName = projectName.trim();
    const trimmedShort = shortDescription.trim();
    const trimmedFull = fullDescription.trim();

    if (trimmedName.length > PROJECT_NAME_MAX) {
      nextErrors.projectName = `Project name must be ${PROJECT_NAME_MAX} characters or less.`;
    }
    if (trimmedShort.length > SHORT_DESCRIPTION_MAX) {
      nextErrors.shortDescription = `Short description must be ${SHORT_DESCRIPTION_MAX} characters or less.`;
    }
    if (trimmedFull.length > FULL_DESCRIPTION_MAX) {
      nextErrors.fullDescription = `Full description must be ${FULL_DESCRIPTION_MAX} characters or less.`;
    }
    if (!hasAtLeastOneUrl) {
      nextErrors.urls =
        'Add at least one project URL: website, GitHub, or demo video.';
    }

    if (trimmedWebsite) {
      if (trimmedWebsite.length > URL_MAX) {
        nextErrors.websiteUrl = `Website URL must be ${URL_MAX} characters or less.`;
      } else if (!isValidHttpUrl(trimmedWebsite)) {
        nextErrors.websiteUrl = 'Please enter a valid http or https URL.';
      }
    }
    if (trimmedGithub) {
      if (trimmedGithub.length > URL_MAX) {
        nextErrors.githubUrl = `GitHub URL must be ${URL_MAX} characters or less.`;
      } else if (!isValidGithubUrl(trimmedGithub)) {
        nextErrors.githubUrl = 'GitHub URL must be a github.com link.';
      }
    }
    if (trimmedDemo) {
      if (trimmedDemo.length > URL_MAX) {
        nextErrors.demoVideoUrl = `Demo video URL must be ${URL_MAX} characters or less.`;
      } else if (!isValidHttpUrl(trimmedDemo)) {
        nextErrors.demoVideoUrl = 'Please enter a valid http or https URL.';
      }
    }

    setErrors(nextErrors);
    const firstError =
      nextErrors.projectName ??
      nextErrors.shortDescription ??
      nextErrors.fullDescription ??
      nextErrors.urls ??
      nextErrors.websiteUrl ??
      nextErrors.githubUrl ??
      nextErrors.demoVideoUrl;

    if (firstError) {
      toast.error({
        title: 'Validation error',
        description: firstError,
      });
      return;
    }

    const payload: ProjectPayload = {
      title: trimmedName,
      short_description: trimmedShort,
      long_description:
        mode === 'edit' ? trimmedFull || null : trimmedFull || undefined,
      demo_url:
        mode === 'edit' ? trimmedWebsite || null : trimmedWebsite || undefined,
      github_url:
        mode === 'edit' ? trimmedGithub || null : trimmedGithub || undefined,
      video_url:
        mode === 'edit' ? trimmedDemo || null : trimmedDemo || undefined,
      categories:
        mode === 'edit'
          ? categories
          : categories.length > 0
            ? categories
            : undefined,
      tags: mode === 'edit' ? tags : tags.length > 0 ? tags : undefined,
      tech_stack:
        mode === 'edit'
          ? techStack
          : techStack.length > 0
            ? techStack
            : undefined,
    };

    onSubmit(payload, {
      title: projectName,
      shortDescription,
      fullDescription,
      imageUrl: initialValues.imageUrl ?? null,
      categories,
      tags,
      techStack,
      websiteUrl,
      githubUrl,
      demoVideoUrl,
    });
  };

  return (
    <form id="project-form" onSubmit={handleSubmit}>
      <Flex gap="24px" align="stretch" flexDir={{ base: 'column', md: 'row' }}>
        <VStack flex={1.4} align="stretch" gap="16px" minW={0}>
          <Box
            bg="gray.100"
            borderRadius="13px"
            p={{ base: '16px', md: '24px' }}
            w="100%"
            flex={1}
            minH={0}
            display="flex"
            flexDir="column"
          >
            <VStack
              align="start"
              gap="16px"
              w="100%"
              flex={1}
              h="100%"
              minH={0}
            >
              <Text
                fontSize="md"
                fontWeight="bold"
                color="gray.900"
                lineHeight="30px"
              >
                Project Details
              </Text>

              <VStack align="start" gap="4px" w="100%">
                <FieldLabel>
                  Project Name{' '}
                  <Text as="span" color="red.500">
                    *
                  </Text>
                </FieldLabel>
                <Input
                  value={projectName}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) => {
                    setProjectName(e.target.value);
                    if (errors.projectName)
                      setErrors((prev) => ({
                        ...prev,
                        projectName: undefined,
                      }));
                  }}
                  placeholder="Give your project a clear name"
                  {...inputBase}
                  h="43px"
                  maxLength={PROJECT_NAME_MAX}
                  borderColor={errors.projectName ? 'red.400' : 'gray.300'}
                />
                <Flex w="100%" justify="flex-end">
                  <Text
                    fontSize="xs"
                    color={
                      projectName.length >= PROJECT_NAME_MAX
                        ? 'red.500'
                        : projectName.length >= PROJECT_NAME_MAX * 0.9
                          ? 'orange.500'
                          : 'gray.500'
                    }
                    fontWeight={
                      projectName.length >= PROJECT_NAME_MAX
                        ? 'semibold'
                        : 'normal'
                    }
                  >
                    {projectName.length}/{PROJECT_NAME_MAX}
                  </Text>
                </Flex>
                {errors.projectName && (
                  <Text fontSize="xs" color="red.500">
                    {errors.projectName}
                  </Text>
                )}
              </VStack>

              <VStack align="start" gap="8px" w="100%">
                <FieldLabel>Project Logo</FieldLabel>
                <input
                  ref={fileInputRef}
                  type="file"
                  accept="image/*"
                  style={{ display: 'none' }}
                  disabled
                />
                <Box
                  w="100%"
                  h="144px"
                  borderRadius="10px"
                  border="1px dashed"
                  borderColor="gray.300"
                  overflow="hidden"
                  opacity={0.75}
                  bg="gray.50"
                  display="flex"
                  alignItems="center"
                  justifyContent="center"
                  px="20px"
                >
                  <VStack gap="6px" textAlign="center">
                    <Text fontSize="sm" fontWeight="semibold" color="gray.600">
                      Project icons aren&apos;t available yet in GatorRank.
                    </Text>
                    <Text fontSize="xs" color="gray.500" lineHeight="18px">
                      You&apos;ll be able to upload a custom icon in a future
                      update.
                    </Text>
                  </VStack>
                </Box>
                <Text fontSize="sm" color="gray.600" lineHeight="20px">
                  Project logos are not available yet.
                </Text>
              </VStack>

              <VStack align="start" gap="4px" w="100%">
                <FieldLabel>
                  Short Description{' '}
                  <Text as="span" color="red.500">
                    *
                  </Text>
                </FieldLabel>
                <Input
                  value={shortDescription}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) => {
                    setShortDescription(e.target.value);
                    if (errors.shortDescription)
                      setErrors((prev) => ({
                        ...prev,
                        shortDescription: undefined,
                      }));
                  }}
                  placeholder="One-line summary of your project"
                  {...inputBase}
                  h="43px"
                  maxLength={SHORT_DESCRIPTION_MAX}
                  borderColor={errors.shortDescription ? 'red.400' : 'gray.300'}
                />
                <Flex w="100%" justify="flex-end">
                  <Text
                    fontSize="xs"
                    color={
                      shortDescription.length >= SHORT_DESCRIPTION_MAX
                        ? 'red.500'
                        : shortDescription.length >=
                            SHORT_DESCRIPTION_MAX * 0.85
                          ? 'orange.500'
                          : 'gray.500'
                    }
                    fontWeight={
                      shortDescription.length >= SHORT_DESCRIPTION_MAX
                        ? 'semibold'
                        : 'normal'
                    }
                  >
                    {shortDescription.length}/{SHORT_DESCRIPTION_MAX}
                  </Text>
                </Flex>
                {errors.shortDescription && (
                  <Text fontSize="xs" color="red.500">
                    {errors.shortDescription}
                  </Text>
                )}
              </VStack>

              <VStack align="start" gap="4px" w="100%" flex={1} minH={0}>
                <FieldLabel>Full Description</FieldLabel>
                <Textarea
                  value={fullDescription}
                  onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => {
                    setFullDescription(e.target.value);
                    if (errors.fullDescription)
                      setErrors((prev) => ({
                        ...prev,
                        fullDescription: undefined,
                      }));
                  }}
                  placeholder="Describe what your project does, how it works, and any interesting details."
                  {...inputBase}
                  flex={1}
                  minH="140px"
                  py="10px"
                  resize="none"
                  maxLength={FULL_DESCRIPTION_MAX}
                  borderColor={errors.fullDescription ? 'red.400' : 'gray.300'}
                />
                <Flex w="100%" justify="flex-end" flexShrink={0}>
                  <Text
                    fontSize="xs"
                    color={
                      fullDescription.length >= FULL_DESCRIPTION_MAX
                        ? 'red.500'
                        : fullDescription.length >= FULL_DESCRIPTION_MAX * 0.9
                          ? 'orange.500'
                          : 'gray.500'
                    }
                    fontWeight={
                      fullDescription.length >= FULL_DESCRIPTION_MAX
                        ? 'semibold'
                        : 'normal'
                    }
                  >
                    {fullDescription.length}/{FULL_DESCRIPTION_MAX}
                  </Text>
                </Flex>
                {errors.fullDescription && (
                  <Text fontSize="xs" color="red.500">
                    {errors.fullDescription}
                  </Text>
                )}
              </VStack>
            </VStack>
          </Box>
        </VStack>

        <VStack flex={1} align="start" gap="16px" minW={0}>
          <Box
            bg="gray.100"
            borderRadius="13px"
            p={{ base: '16px', md: '24px' }}
            w="100%"
          >
            <VStack align="start" gap="10px" w="100%">
              <Text
                fontSize="md"
                fontWeight="bold"
                color="gray.900"
                lineHeight="30px"
              >
                Visibility
              </Text>
              <Text fontSize="sm" color="gray.500" lineHeight="24px">
                Published projects appear on your profile. Drafts stay hidden
                until you publish them.
              </Text>
              <HStack
                as="label"
                gap="10px"
                cursor={isBusy ? 'not-allowed' : 'pointer'}
              >
                <input
                  type="checkbox"
                  checked={publishChecked}
                  disabled={isBusy}
                  onChange={(e) => onPublishCheckedChange(e.target.checked)}
                />
                <Text fontSize="sm" color="gray.900" lineHeight="20px">
                  Publish this project
                </Text>
              </HStack>
            </VStack>
          </Box>

          <ProjectTermField
            title="Categories"
            singularLabel="category"
            placeholder="Start typing a category"
            helperText={`Type your own categories or pick from suggestions. You can add up to ${CATEGORY_LIMIT} categories.`}
            values={categories}
            limit={CATEGORY_LIMIT}
            loadTerms={listCategories}
            loadingText="Loading category suggestions..."
            loadErrorText="Could not load categories."
            onChange={setCategories}
          />

          <ProjectTermField
            title="Tags"
            singularLabel="tag"
            placeholder="Start typing a tag"
            helperText={`Type your own tags or pick from suggestions. You can add up to ${TAG_LIMIT} tags to help others discover your project.`}
            values={tags}
            limit={TAG_LIMIT}
            loadTerms={listTags}
            loadingText="Loading tag suggestions..."
            loadErrorText="Could not load tags."
            onChange={setTags}
          />

          <ProjectTermField
            title="Tech Stack"
            singularLabel="tech stack term"
            placeholder="Start typing a tech stack term"
            helperText={`Type your own tech stack terms or pick from suggestions. You can add up to ${TECH_STACK_LIMIT} tech stack terms.`}
            values={techStack}
            limit={TECH_STACK_LIMIT}
            loadTerms={listTechStacks}
            loadingText="Loading tech stack suggestions..."
            loadErrorText="Could not load tech stack terms."
            onChange={setTechStack}
          />

          <Box
            bg="gray.100"
            borderRadius="13px"
            p={{ base: '16px', md: '24px' }}
            w="100%"
          >
            <VStack align="start" gap="12px" w="100%">
              <Text
                fontSize="md"
                fontWeight="bold"
                color="gray.900"
                lineHeight="30px"
              >
                Team Members
              </Text>
              <FieldLabel>
                List teammates by their @ufl.edu email address.
              </FieldLabel>
              <HStack gap="8px" w="100%">
                <Input
                  value={memberInput}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                    setMemberInput(e.target.value)
                  }
                  onKeyDown={(e: React.KeyboardEvent) => {
                    if (e.key === 'Enter') {
                      e.preventDefault();
                      void handleAddMember();
                    }
                  }}
                  placeholder="name@ufl.edu"
                  {...inputBase}
                  h="40px"
                  flex={1}
                />
                <Button
                  type="button"
                  aria-label="Add team member"
                  bg="orange.400"
                  color="white"
                  borderRadius="10px"
                  h="40px"
                  px="10px"
                  _hover={{ bg: 'orange.500' }}
                  onClick={() => {
                    void handleAddMember();
                  }}
                  disabled={isBusy || memberSubmitting}
                >
                  <LuPlus size={16} />
                </Button>
              </HStack>
              <MemberPills
                members={members}
                pendingMembers={normalizedPendingMembers}
                onRemoveMember={(idOrEmail) => {
                  void handleRemoveMember(idOrEmail);
                }}
                onUpdateMemberRole={(userId, role) => {
                  void handleUpdateMemberRole(userId, role);
                }}
                onUpdatePendingMemberRole={handleUpdatePendingMemberRole}
                pendingRoleUpdates={pendingRoleUpdates}
                isBusy={isBusy || memberSubmitting}
              />
            </VStack>
          </Box>

          <Box
            bg="gray.100"
            borderRadius="13px"
            p={{ base: '16px', md: '24px' }}
            w="100%"
          >
            <VStack align="start" gap="12px" w="100%">
              <Text
                fontSize="md"
                fontWeight="bold"
                color="gray.900"
                lineHeight="30px"
              >
                Links
              </Text>
              <FieldLabel>
                Add at least one project URL so people can visit your work.
              </FieldLabel>

              {errors.urls && (
                <Text fontSize="sm" color="red.500">
                  {errors.urls}
                </Text>
              )}

              <VStack align="start" gap="4px" w="100%">
                <FieldLabel>Website Link URL</FieldLabel>
                <HStack gap="10px" w="100%">
                  <Box color="gray.500" flexShrink={0}>
                    <LuGlobe size={18} />
                  </Box>
                  <Input
                    value={websiteUrl}
                    onChange={(e: React.ChangeEvent<HTMLInputElement>) => {
                      setWebsiteUrl(e.target.value);
                      if (errors.websiteUrl || errors.urls)
                        setErrors((prev) => ({
                          ...prev,
                          websiteUrl: undefined,
                          urls: undefined,
                        }));
                    }}
                    placeholder="https://yourproject.com"
                    {...inputBase}
                    h="36px"
                    maxLength={URL_MAX}
                    borderColor={errors.websiteUrl ? 'red.400' : 'gray.300'}
                  />
                </HStack>
                {errors.websiteUrl && (
                  <Text fontSize="xs" color="red.500">
                    {errors.websiteUrl}
                  </Text>
                )}
              </VStack>

              <VStack align="start" gap="4px" w="100%">
                <FieldLabel>GitHub Repository</FieldLabel>
                <HStack gap="10px" w="100%">
                  <Box color="gray.500" flexShrink={0}>
                    <LuGithub size={18} />
                  </Box>
                  <Input
                    value={githubUrl}
                    onChange={(e: React.ChangeEvent<HTMLInputElement>) => {
                      setGithubUrl(e.target.value);
                      if (errors.githubUrl || errors.urls)
                        setErrors((prev) => ({
                          ...prev,
                          githubUrl: undefined,
                          urls: undefined,
                        }));
                    }}
                    placeholder="https://github.com/user/repo"
                    {...inputBase}
                    h="36px"
                    maxLength={URL_MAX}
                    borderColor={errors.githubUrl ? 'red.400' : 'gray.300'}
                  />
                </HStack>
                {errors.githubUrl && (
                  <Text fontSize="xs" color="red.500">
                    {errors.githubUrl}
                  </Text>
                )}
              </VStack>

              <VStack align="start" gap="4px" w="100%">
                <FieldLabel>Demo Video URL</FieldLabel>
                <HStack gap="10px" w="100%">
                  <Box color="gray.500" flexShrink={0}>
                    <LuPlay size={18} />
                  </Box>
                  <Input
                    value={demoVideoUrl}
                    onChange={(e: React.ChangeEvent<HTMLInputElement>) => {
                      setDemoVideoUrl(e.target.value);
                      if (errors.demoVideoUrl || errors.urls)
                        setErrors((prev) => ({
                          ...prev,
                          demoVideoUrl: undefined,
                          urls: undefined,
                        }));
                    }}
                    placeholder="https://youtu.be/..."
                    {...inputBase}
                    h="36px"
                    maxLength={URL_MAX}
                    borderColor={errors.demoVideoUrl ? 'red.400' : 'gray.300'}
                  />
                </HStack>
                {errors.demoVideoUrl && (
                  <Text fontSize="xs" color="red.500">
                    {errors.demoVideoUrl}
                  </Text>
                )}
              </VStack>
            </VStack>
          </Box>
        </VStack>
      </Flex>
    </form>
  );
}

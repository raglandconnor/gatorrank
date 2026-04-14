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
import { listTags } from '@/lib/api/taxonomy';
import type { ProjectMemberInfo, TaxonomyTerm } from '@/lib/api/types/project';
import { toast } from '@/lib/ui/toast';

const PROJECT_NAME_MAX = 50;
const SHORT_DESCRIPTION_MAX = 280;
const FULL_DESCRIPTION_MAX = 5000;
const URL_MAX = 2048;
const TAG_LIMIT = 10;

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

function MemberPills({
  members,
  pendingEmails,
  onRemoveMember,
  isBusy,
}: {
  members: ProjectMemberInfo[];
  pendingEmails: string[];
  onRemoveMember: (idOrEmail: string) => void;
  isBusy: boolean;
}) {
  if (members.length === 0 && pendingEmails.length === 0) return null;

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

      {pendingEmails.map((email) => (
        <HStack
          key={email}
          gap="4px"
          px="10px"
          py="4px"
          borderRadius="10px"
          bg="white"
          border="1px solid"
          borderColor="gray.300"
        >
          <Text fontSize="sm" color="gray.700" lineHeight="20px">
            {email}
          </Text>
          <Button
            type="button"
            aria-label={`Remove ${email}`}
            variant="ghost"
            size="xs"
            minW="auto"
            h="auto"
            p={0}
            disabled={isBusy}
            onClick={() => onRemoveMember(email)}
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
  tags: string[];
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
  tags?: string[];
}

interface ProjectFormProps {
  mode: ProjectFormMode;
  initialValues: ProjectFormValues;
  onSubmit: (payload: ProjectPayload, values: ProjectFormValues) => void;
  onValidityChange?: (isDisabled: boolean) => void;
  publishChecked: boolean;
  onPublishCheckedChange: (checked: boolean) => void;
  members?: ProjectMemberInfo[];
  pendingMemberEmails?: string[];
  onAddMember: (
    email: string,
  ) => Promise<{ ok: true } | { ok: false; message: string }>;
  onRemoveMember: (
    idOrEmail: string,
  ) => Promise<{ ok: true } | { ok: false; message: string }>;
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
  pendingMemberEmails = [],
  onAddMember,
  onRemoveMember,
  isBusy = false,
}: ProjectFormProps) {
  const [projectName, setProjectName] = useState(initialValues.title);
  const [shortDescription, setShortDescription] = useState(
    initialValues.shortDescription,
  );
  const [fullDescription, setFullDescription] = useState(
    initialValues.fullDescription,
  );
  const [tags, setTags] = useState<string[]>(initialValues.tags);
  const [tagInput, setTagInput] = useState('');
  const [availableTags, setAvailableTags] = useState<TaxonomyTerm[]>([]);
  const [tagsLoading, setTagsLoading] = useState(true);
  const [tagsError, setTagsError] = useState<string | null>(null);

  const [memberInput, setMemberInput] = useState('');
  const [memberSubmitting, setMemberSubmitting] = useState(false);
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

  function normalizeTagName(value: string): string {
    return value.trim().toLowerCase();
  }

  function containsControlChars(value: string): boolean {
    return /[\u0000-\u001F\u007F-\u009F]/.test(value);
  }

  useEffect(() => {
    let cancelled = false;

    async function loadAvailableTags() {
      try {
        setTagsLoading(true);
        const terms = await listTags();
        if (cancelled) return;
        setAvailableTags(terms);
        setTagsError(null);
      } catch (error) {
        if (cancelled) return;
        setTagsError(
          error instanceof Error ? error.message : 'Could not load tags.',
        );
      } finally {
        if (!cancelled) {
          setTagsLoading(false);
        }
      }
    }

    void loadAvailableTags();

    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    setProjectName(initialValues.title);
    setShortDescription(initialValues.shortDescription);
    setFullDescription(initialValues.fullDescription);
    setTags(initialValues.tags);
    setTagInput('');
    setWebsiteUrl(initialValues.websiteUrl);
    setGithubUrl(initialValues.githubUrl);
    setDemoVideoUrl(initialValues.demoVideoUrl);
  }, [initialValues]);

  const trimmedWebsite = websiteUrl.trim();
  const trimmedGithub = githubUrl.trim();
  const trimmedDemo = demoVideoUrl.trim();
  const hasAtLeastOneUrl = Boolean(
    trimmedWebsite || trimmedGithub || trimmedDemo,
  );

  const normalizedTagInput = tagInput.trim().toLowerCase();
  const filteredTags = useMemo(
    () =>
      availableTags
        .filter(
          (term) =>
            !tags.some(
              (selected) =>
                normalizeTagName(selected) === normalizeTagName(term.name),
            ) &&
            (!normalizedTagInput ||
              term.name.toLowerCase().includes(normalizedTagInput)),
        )
        .slice(0, 8),
    [availableTags, normalizedTagInput, tags],
  );

  const isSubmitDisabled =
    !projectName.trim() || !shortDescription.trim() || !hasAtLeastOneUrl;

  useEffect(() => {
    onValidityChange?.(isSubmitDisabled);
  }, [isSubmitDisabled, onValidityChange]);

  const addTag = (name: string) => {
    const trimmed = name.trim();
    if (!trimmed) return;
    if (
      tags.some(
        (existingTag) =>
          normalizeTagName(existingTag) === normalizeTagName(trimmed),
      )
    ) {
      toast.error({
        title: 'Duplicate tag',
        description: 'That tag has already been added to this project.',
      });
      return;
    }
    if (tags.length >= TAG_LIMIT) {
      toast.error({
        title: 'Tag limit reached',
        description: `You can add up to ${TAG_LIMIT} tags to a project.`,
      });
      return;
    }

    if (trimmed.length < 2 || trimmed.length > 64) {
      toast.error({
        title: 'Invalid tag',
        description: 'Tags must be between 2 and 64 characters long.',
      });
      return;
    }

    if (containsControlChars(trimmed)) {
      toast.error({
        title: 'Invalid tag',
        description: 'Tags cannot include control characters.',
      });
      return;
    }

    setTags((prev) => [...prev, trimmed]);
    setTagInput('');
  };

  const handleAddTag = () => {
    const normalized = tagInput.trim().toLowerCase();
    if (!normalized) return;

    const exact = availableTags.find(
      (term) => term.name.toLowerCase() === normalized,
    );

    if (exact) {
      addTag(exact.name);
      return;
    }

    addTag(tagInput);
  };

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
      const result = await onAddMember(normalized);

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
      tags: mode === 'edit' ? tags : tags.length > 0 ? tags : undefined,
    };

    onSubmit(payload, {
      title: projectName,
      shortDescription,
      fullDescription,
      imageUrl: initialValues.imageUrl ?? null,
      tags,
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
                Tags
              </Text>
              <FieldLabel>
                Type your own tags or pick from suggestions. You can add up to{' '}
                {TAG_LIMIT} tags to help others discover your project.
              </FieldLabel>

              <HStack gap="8px" w="100%">
                <Input
                  value={tagInput}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                    setTagInput(e.target.value)
                  }
                  onKeyDown={(e: React.KeyboardEvent) => {
                    if (e.key === 'Enter') {
                      e.preventDefault();
                      handleAddTag();
                    }
                  }}
                  placeholder="Start typing a tag"
                  {...inputBase}
                  h="40px"
                  flex={1}
                />
                <Button
                  type="button"
                  aria-label="Add tag"
                  bg="orange.400"
                  color="white"
                  borderRadius="10px"
                  h="40px"
                  px="10px"
                  _hover={{ bg: 'orange.500' }}
                  onClick={handleAddTag}
                >
                  <LuPlus size={16} />
                </Button>
              </HStack>

              {tagsLoading ? (
                <HStack gap="8px">
                  <Spinner size="sm" color="orange.400" />
                  <Text fontSize="sm" color="gray.500">
                    Loading tag suggestions...
                  </Text>
                </HStack>
              ) : tagsError ? (
                <Text fontSize="sm" color="orange.600">
                  {tagsError} You can still add your own tags manually.
                </Text>
              ) : normalizedTagInput && filteredTags.length > 0 ? (
                <Wrap gap="8px">
                  {filteredTags.map((term) => (
                    <Button
                      key={term.id}
                      type="button"
                      size="sm"
                      variant="outline"
                      borderColor="orange.200"
                      bg="white"
                      color="gray.700"
                      _hover={{ bg: 'orange.50' }}
                      onClick={() => addTag(term.name)}
                    >
                      <HStack gap="6px">
                        <LuTag size={13} />
                        <Text>{term.name}</Text>
                      </HStack>
                    </Button>
                  ))}
                </Wrap>
              ) : null}

              {tags.length > 0 && (
                <Wrap gap="8px">
                  {tags.map((tag) => (
                    <HStack
                      key={tag}
                      gap="4px"
                      bg="white"
                      border="1px solid"
                      borderColor="orange.200"
                      borderRadius="10px"
                      px="10px"
                      py="4px"
                    >
                      <Text fontSize="sm" color="gray.700" lineHeight="20px">
                        {tag}
                      </Text>
                      <Button
                        type="button"
                        aria-label={`Remove ${tag}`}
                        variant="ghost"
                        size="xs"
                        minW="auto"
                        h="auto"
                        p={0}
                        onClick={() =>
                          setTags((prev) =>
                            prev.filter((value) => value !== tag),
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
                pendingEmails={pendingMemberEmails}
                onRemoveMember={(idOrEmail) => {
                  void handleRemoveMember(idOrEmail);
                }}
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

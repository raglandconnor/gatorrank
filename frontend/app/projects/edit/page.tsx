'use client';

import { useRef, useState } from 'react';
import { useRouter } from 'next/navigation';
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
} from '@chakra-ui/react';
import {
  LuPlus,
  LuX,
  LuGlobe,
  LuGithub,
  LuPlay,
  LuImage,
  LuSave,
} from 'react-icons/lu';
import { Navbar } from '@/components/Navbar';
import { toaster } from '@/components/ui/toaster';
import { mockProject } from '@/data/mock-project';

const PROJECT_NAME_MAX = 50;
const SHORT_DESCRIPTION_MAX = 70;
const FULL_DESCRIPTION_MAX = 2000;
const URL_MAX = 2048;

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

function TagPills({
  items,
  onRemove,
}: {
  items: string[];
  onRemove: (value: string) => void;
}) {
  return (
    <Wrap gap="8px">
      {items.map((item) => (
        <HStack
          key={item}
          gap="4px"
          px="10px"
          py="4px"
          borderRadius="10px"
          bg="white"
          border="1px solid"
          borderColor="gray.300"
        >
          <Text fontSize="sm" color="gray.700" lineHeight="20px">
            {item}
          </Text>
          <Button
            type="button"
            aria-label={`Remove ${item}`}
            variant="ghost"
            size="xs"
            minW="auto"
            h="auto"
            p={0}
            onClick={() => onRemove(item)}
          >
            <LuX size={12} />
          </Button>
        </HStack>
      ))}
    </Wrap>
  );
}

export default function EditProjectPage() {
  const router = useRouter();

  const [projectName, setProjectName] = useState(mockProject.name);
  const [shortDescription, setShortDescription] = useState(
    mockProject.shortDescription,
  );
  const [fullDescription, setFullDescription] = useState(
    mockProject.fullDescription,
  );

  const fileInputRef = useRef<HTMLInputElement>(null);
  const [logoPreview, setLogoPreview] = useState<string | null>(
    mockProject.imageUrl ?? null,
  );

  const [tagInput, setTagInput] = useState('');
  const [tags, setTags] = useState<string[]>(mockProject.tags);

  const [memberInput, setMemberInput] = useState('');
  const [teamMembers, setTeamMembers] = useState<string[]>(
    mockProject.teamMembers,
  );

  const [websiteUrl, setWebsiteUrl] = useState(mockProject.websiteUrl);
  const [githubUrl, setGithubUrl] = useState(mockProject.githubUrl);
  const [demoVideoUrl, setDemoVideoUrl] = useState(mockProject.demoVideoUrl);

  const [errors, setErrors] = useState<{
    projectName?: string;
    shortDescription?: string;
    fullDescription?: string;
    websiteUrl?: string;
    githubUrl?: string;
    demoVideoUrl?: string;
  }>({});

  const addTag = () => {
    const value = tagInput.trim();
    if (!value) return;
    setTags((prev: string[]) =>
      prev.includes(value) ? prev : [...prev, value],
    );
    setTagInput('');
  };

  const removeTag = (value: string) => {
    setTags((prev: string[]) => prev.filter((t) => t !== value));
  };

  const addMember = () => {
    const value = memberInput.trim();
    if (!value) return;
    if (!isValidUflEmail(value)) {
      toaster.error({
        title: 'Invalid email',
        description: 'Team members must use a valid @ufl.edu email address.',
      });
      return;
    }
    setTeamMembers((prev: string[]) =>
      prev.includes(value) ? prev : [...prev, value],
    );
    setMemberInput('');
  };

  const removeMember = (value: string) => {
    setTeamMembers((prev: string[]) => prev.filter((m) => m !== value));
  };

  const handleLogoChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const previewUrl = URL.createObjectURL(file);
    setLogoPreview(previewUrl);

    e.target.value = '';
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const isSubmitDisabled =
    !projectName.trim() ||
    !shortDescription.trim() ||
    !fullDescription.trim() ||
    !logoPreview;

  const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (isSubmitDisabled) return;

    const nextErrors: typeof errors = {};

    if (projectName.trim().length > PROJECT_NAME_MAX) {
      nextErrors.projectName = `Project name must be ${PROJECT_NAME_MAX} characters or less.`;
    }
    if (shortDescription.trim().length > SHORT_DESCRIPTION_MAX) {
      nextErrors.shortDescription = `Short description must be ${SHORT_DESCRIPTION_MAX} characters or less.`;
    }
    if (fullDescription.trim().length > FULL_DESCRIPTION_MAX) {
      nextErrors.fullDescription = `Full description must be ${FULL_DESCRIPTION_MAX} characters or less.`;
    }

    if (websiteUrl.trim()) {
      if (websiteUrl.length > URL_MAX) {
        nextErrors.websiteUrl = `Website URL must be ${URL_MAX} characters or less.`;
      } else if (!isValidHttpUrl(websiteUrl)) {
        nextErrors.websiteUrl = 'Please enter a valid http or https URL.';
      }
    }
    if (githubUrl.trim()) {
      if (githubUrl.length > URL_MAX) {
        nextErrors.githubUrl = `GitHub URL must be ${URL_MAX} characters or less.`;
      } else if (!isValidGithubUrl(githubUrl)) {
        nextErrors.githubUrl = 'GitHub URL must be a github.com link.';
      }
    }
    if (demoVideoUrl.trim()) {
      if (demoVideoUrl.length > URL_MAX) {
        nextErrors.demoVideoUrl = `Demo video URL must be ${URL_MAX} characters or less.`;
      } else if (!isValidHttpUrl(demoVideoUrl)) {
        nextErrors.demoVideoUrl = 'Please enter a valid http or https URL.';
      }
    }

    setErrors(nextErrors);
    const firstError =
      nextErrors.projectName ??
      nextErrors.shortDescription ??
      nextErrors.fullDescription ??
      nextErrors.websiteUrl ??
      nextErrors.githubUrl ??
      nextErrors.demoVideoUrl;
    if (firstError) {
      toaster.error({
        title: 'Validation error',
        description: firstError,
      });
      return;
    }

    toaster.success({
      title: 'Project updated',
      description: `"${projectName.trim()}" has been successfully updated.`,
    });

    router.push(`/projects/${mockProject.id}`);
  };

  const handleCancel = () => {
    router.push(`/projects/${mockProject.id}`);
  };

  return (
    <Box minH="100vh" bg="white">
      <Navbar />
      <Box px="36px" pt="32px" pb="64px" maxW="1280px" mx="auto">
        <form onSubmit={handleSubmit}>
          {/* Header */}
          <Flex align="flex-start" justify="space-between" mb="32px" gap="16px">
            <VStack align="start" gap="6px">
              <Text
                fontSize="xl"
                fontWeight="bold"
                color="gray.900"
                lineHeight="32px"
              >
                Edit Project
              </Text>
              <Text
                fontSize="sm"
                color="gray.600"
                lineHeight="24px"
                maxW="520px"
              >
                Update your project details for the GatorRank community.
              </Text>
            </VStack>

            <HStack gap="12px" flexShrink={0}>
              <Button
                type="button"
                variant="outline"
                border="1px solid"
                borderColor="orange.400"
                borderRadius="14px"
                h="44px"
                px="20px"
                fontSize="sm"
                color="gray.900"
                bg="white"
                _hover={{ bg: 'orange.50' }}
                transition="background 0.15s"
                onClick={handleCancel}
              >
                <HStack gap="6px">
                  <LuX size={16} />
                  <Text>Cancel</Text>
                </HStack>
              </Button>
              <Button
                type="submit"
                bg="orange.400"
                color="white"
                borderRadius="14px"
                h="44px"
                px="20px"
                fontSize="sm"
                fontWeight="normal"
                _hover={{ bg: isSubmitDisabled ? 'orange.400' : 'orange.500' }}
                transition="background 0.15s"
                disabled={isSubmitDisabled}
              >
                <HStack gap="6px">
                  <LuSave size={16} />
                  <Text>Save Changes</Text>
                </HStack>
              </Button>
            </HStack>
          </Flex>

          {/* Main layout */}
          <Flex
            gap="24px"
            align="stretch"
            flexDir={{ base: 'column', md: 'row' }}
          >
            {/* Left column: required fields */}
            <VStack flex={1.4} align="stretch" gap="16px" minW={0}>
              <Box
                bg="gray.100"
                borderRadius="13px"
                p="24px"
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

                  {/* Project name */}
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

                  {/* Project logo */}
                  <VStack align="start" gap="8px" w="100%">
                    <FieldLabel>
                      Project Logo{' '}
                      <Text as="span" color="red.500">
                        *
                      </Text>
                    </FieldLabel>
                    <input
                      ref={fileInputRef}
                      type="file"
                      accept="image/*"
                      style={{ display: 'none' }}
                      onChange={handleLogoChange}
                    />
                    <Box
                      w={logoPreview ? '144px' : '100%'}
                      h="144px"
                      bg="white"
                      borderRadius="10px"
                      border="1px dashed"
                      borderColor="gray.300"
                      display="flex"
                      alignItems="center"
                      justifyContent="center"
                      cursor="pointer"
                      overflow="hidden"
                      onClick={() => fileInputRef.current?.click()}
                    >
                      {logoPreview ? (
                        // eslint-disable-next-line @next/next/no-img-element
                        <img
                          src={logoPreview}
                          alt="Project logo preview"
                          style={{
                            width: '100%',
                            height: '100%',
                            objectFit: 'cover',
                            borderRadius: '10px',
                          }}
                        />
                      ) : (
                        <VStack gap="4px">
                          <Box color="gray.500">
                            <LuImage size={22} />
                          </Box>
                          <Text
                            fontSize="sm"
                            color="gray.600"
                            lineHeight="20px"
                            textAlign="center"
                          >
                            Click to upload a project logo
                          </Text>
                        </VStack>
                      )}
                    </Box>
                  </VStack>

                  {/* Short description */}
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
                      borderColor={
                        errors.shortDescription ? 'red.400' : 'gray.300'
                      }
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

                  {/* Full description */}
                  <VStack align="start" gap="4px" w="100%" flex={1} minH={0}>
                    <FieldLabel>
                      Full Description{' '}
                      <Text as="span" color="red.500">
                        *
                      </Text>
                    </FieldLabel>
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
                      borderColor={
                        errors.fullDescription ? 'red.400' : 'gray.300'
                      }
                    />
                    <Flex w="100%" justify="flex-end" flexShrink={0}>
                      <Text
                        fontSize="xs"
                        color={
                          fullDescription.length >= FULL_DESCRIPTION_MAX
                            ? 'red.500'
                            : fullDescription.length >=
                                FULL_DESCRIPTION_MAX * 0.9
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

            {/* Right column: optional metadata */}
            <VStack flex={1} align="start" gap="16px" minW={0}>
              {/* Tags */}
              <Box bg="gray.100" borderRadius="13px" p="24px" w="100%">
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
                    Add topics or technologies to help others discover your
                    project.
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
                          addTag();
                        }
                      }}
                      placeholder="e.g., React, Python, ML..."
                      {...inputBase}
                      h="40px"
                      flex={1}
                    />
                    <Button
                      type="button"
                      bg="orange.400"
                      color="white"
                      borderRadius="10px"
                      h="40px"
                      px="10px"
                      _hover={{ bg: 'orange.500' }}
                      onClick={addTag}
                    >
                      <LuPlus size={16} />
                    </Button>
                  </HStack>
                  {tags.length > 0 && (
                    <TagPills items={tags} onRemove={removeTag} />
                  )}
                </VStack>
              </Box>

              {/* Team members */}
              <Box bg="gray.100" borderRadius="13px" p="24px" w="100%">
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
                          addMember();
                        }
                      }}
                      placeholder="name@ufl.edu"
                      {...inputBase}
                      h="40px"
                      flex={1}
                    />
                    <Button
                      type="button"
                      bg="orange.400"
                      color="white"
                      borderRadius="10px"
                      h="40px"
                      px="10px"
                      _hover={{ bg: 'orange.500' }}
                      onClick={addMember}
                    >
                      <LuPlus size={16} />
                    </Button>
                  </HStack>
                  {teamMembers.length > 0 && (
                    <TagPills items={teamMembers} onRemove={removeMember} />
                  )}
                </VStack>
              </Box>

              {/* Links */}
              <Box bg="gray.100" borderRadius="13px" p="24px" w="100%">
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
                    Share where people can see your project online.
                  </FieldLabel>

                  {/* Website URL */}
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
                          if (errors.websiteUrl)
                            setErrors((prev) => ({
                              ...prev,
                              websiteUrl: undefined,
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

                  {/* GitHub URL */}
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
                          if (errors.githubUrl)
                            setErrors((prev) => ({
                              ...prev,
                              githubUrl: undefined,
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

                  {/* Demo video URL */}
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
                          if (errors.demoVideoUrl)
                            setErrors((prev) => ({
                              ...prev,
                              demoVideoUrl: undefined,
                            }));
                        }}
                        placeholder="https://youtu.be/..."
                        {...inputBase}
                        h="36px"
                        maxLength={URL_MAX}
                        borderColor={
                          errors.demoVideoUrl ? 'red.400' : 'gray.300'
                        }
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
      </Box>
    </Box>
  );
}

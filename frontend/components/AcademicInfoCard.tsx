import { Box, VStack, Text, Wrap } from '@chakra-ui/react';

export interface AcademicProfile {
  major: string;
  graduationYear: number;
  courses: string[];
}

interface AcademicInfoCardProps {
  profile: AcademicProfile;
  isOwn: boolean;
}

export function AcademicInfoCard({ profile, isOwn }: AcademicInfoCardProps) {
  const allEmpty =
    !profile.major &&
    profile.graduationYear <= 0 &&
    profile.courses.length === 0;

  // Visitors see nothing when all fields are empty — parent will show a consolidated message.
  if (!isOwn && allEmpty) return null;

  return (
    <Box bg="gray.100" borderRadius="13px" p="24px" w="344px" flexShrink={0}>
      <VStack align="start" gap="16px">
        <Text
          fontSize="md"
          fontWeight="bold"
          color="gray.900"
          lineHeight="30px"
        >
          Academic Information
        </Text>

        <VStack align="start" gap="12px" w="100%">
          {/* Major */}
          {(profile.major || isOwn) && (
            <VStack align="start" gap="2px">
              <Text fontSize="sm" color="gray.500" lineHeight="24px">
                Major
              </Text>
              <Text fontSize="sm" color="gray.900" lineHeight="24px">
                {profile.major || (
                  <Text as="span" color="gray.400">
                    Not set
                  </Text>
                )}
              </Text>
            </VStack>
          )}

          {/* Graduation Year */}
          {(profile.graduationYear > 0 || isOwn) && (
            <VStack align="start" gap="2px">
              <Text fontSize="sm" color="gray.500" lineHeight="24px">
                Graduation Year
              </Text>
              <Text fontSize="sm" color="gray.900" lineHeight="24px">
                {profile.graduationYear > 0 ? (
                  profile.graduationYear
                ) : (
                  <Text as="span" color="gray.400">
                    Not set
                  </Text>
                )}
              </Text>
            </VStack>
          )}

          {/* UF Courses */}
          {(profile.courses.length > 0 || isOwn) && (
            <VStack align="start" gap="8px" w="100%">
              <Text fontSize="sm" color="gray.500" lineHeight="24px">
                UF Courses
              </Text>
              {profile.courses.length > 0 ? (
                <Wrap gap="8px">
                  {profile.courses.map((course) => (
                    <Box
                      key={course}
                      bg="white"
                      border="1.6px solid"
                      borderColor="orange.200"
                      borderRadius="8px"
                      px="10px"
                      py="6px"
                    >
                      <Text fontSize="sm" color="gray.900" lineHeight="24px">
                        {course}
                      </Text>
                    </Box>
                  ))}
                </Wrap>
              ) : (
                <Text fontSize="sm" color="gray.400" lineHeight="24px">
                  No courses added yet.
                </Text>
              )}
            </VStack>
          )}
        </VStack>
      </VStack>
    </Box>
  );
}
